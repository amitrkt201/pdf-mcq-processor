import os
import fitz
import pytesseract
import cv2
import pandas as pd
import numpy as np
import re
import uuid
import shutil
import zipfile
from PIL import Image
from celery import current_task
from .utils.ocr_utils import enhance_image_for_ocr
from .utils.language_utils import separate_languages, detect_qa_structure

class PDFProcessor:
    def __init__(self, pdf_type, file_urls, options):
        self.pdf_type = pdf_type
        self.file_urls = file_urls
        self.options = options
        self.task_id = str(uuid.uuid4())
        self.images = []
        self.results = []
        self.app = current_task.app
        
    def download_file(self, url):
        # In production, implement actual download from WordPress
        return url  # Placeholder
        
    def convert_to_images(self):
        images = []
        total_pages = 0
        
        for i, url in enumerate(self.file_urls):
            file_path = self.download_file(url)
            doc = fitz.open(file_path)
            start_page = self.options.get('start_page', 0)
            end_page = min(self.options.get('end_page', self.app.conf.MAX_PAGES), len(doc))
            skip_pages = set(self.options.get('skip_pages', []))
            
            for page_num in range(start_page, end_page):
                if page_num in skip_pages: 
                    continue
                    
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=200)
                img_path = f"{self.app.conf.UPLOAD_DIR}/{self.task_id}_p{i}_{page_num}.png"
                pix.save(img_path)
                images.append(img_path)
                total_pages += 1
                
                # Update progress
                current_task.update_state(
                    state='CONVERTING',
                    meta={
                        'progress': 10 + int(40 * len(images) / total_pages),
                        'stage': f'Converting page {len(images)}/{total_pages}',
                        'current_page': len(images)
                    }
                )
                
            doc.close()
        return images, total_pages
        
    def process_image(self, img_path, page_idx, total_pages):
        img = cv2.imread(img_path)
        processed_images = []
        
        # Preprocessing
        enhanced_img = enhance_image_for_ocr(img)
        
        # Two-column detection
        if self.options.get('two_column', False):
            mid = enhanced_img.shape[1] // 2
            left = enhanced_img[:, :mid]
            right = enhanced_img[:, mid:]
            processed_images = [left, right]
        else:
            processed_images = [enhanced_img]
            
        texts = []
        for img_block in processed_images:
            custom_config = r'--oem 3 --psm 6'
            if self.options.get('custom_words'):
                custom_config += f' --user-words {self.options["custom_words"]}'
                
            text = pytesseract.image_to_string(
                Image.fromarray(img_block), 
                lang='hin+eng',
                config=custom_config
            )
            texts.append(text)
            
            # Update progress
            current_task.update_state(
                state='OCR',
                meta={
                    'progress': 50 + int(30 * (page_idx + 0.5) / total_pages),
                    'stage': f'OCR page {page_idx+1}/{total_pages}',
                    'current_page': page_idx+1
                }
            )
            
        return '\n\n'.join(texts)
        
    def process(self):
        try:
            # Step 1: Convert PDFs to images
            self.images, total_pages = self.convert_to_images()
            
            # Step 2: OCR and process each page
            for idx, img_path in enumerate(self.images):
                ocr_text = self.process_image(img_path, idx, total_pages)
                qa_data = detect_qa_structure(
                    ocr_text, 
                    self.options.get('detect_words', '')
                )
                
                # Language separation for bilingual types
                if self.pdf_type in [1, 3]:
                    qa_data['hindi'], qa_data['english'] = separate_languages(
                        f"{qa_data['question']}\n{qa_data['options']}"
                    )
                
                self.results.append(qa_data)
                
                # Update progress
                current_task.update_state(
                    state='PARSING',
                    meta={
                        'progress': 80 + int(10 * idx / total_pages),
                        'stage': f'Parsing page {idx+1}/{total_pages}',
                        'current_page': idx+1
                    }
                )
            
            # Step 3: Generate outputs
            output_paths = self.generate_outputs()
            
            # Step 4: Cleanup if not saving images
            if not self.options.get('save_images', False):
                for img_path in self.images:
                    if os.path.exists(img_path):
                        os.remove(img_path)
            
            return {
                'outputs': output_paths,
                'images': self.images if self.options.get('save_images') else []
            }
            
        except Exception as e:
            current_task.update_state(
                state='FAILURE',
                meta={'error': str(e)}
            )
            raise
            
    def generate_outputs(self):
        output_paths = []
        base_path = f"{self.app.conf.OUTPUT_DIR}/{self.task_id}"
        
        # Prepare data frames
        hindi_data = []
        english_data = []
        
        for res in self.results:
            hindi_data.append({
                'question': res.get('hindi', res['question']),
                'options': res['options'],
                'answer': res['answer'],
                'explanation': res['explanation']
            })
            english_data.append({
                'question': res.get('english', res['question']),
                'options': res['options'],
                'answer': res['answer'],
                'explanation': res['explanation']
            })
        
        # Generate CSV files
        if self.options.get('output_format', 'csv') in ['csv', 'both']:
            pd.DataFrame(hindi_data).to_csv(f"{base_path}_hindi.csv", index=False)
            pd.DataFrame(english_data).to_csv(f"{base_path}_english.csv", index=False)
            output_paths.extend([f"{base_path}_hindi.csv", f"{base_path}_english.csv"])
        
        # Generate Excel file
        if self.options.get('output_format') in ['excel', 'both']:
            with pd.ExcelWriter(f"{base_path}.xlsx") as writer:
                pd.DataFrame(hindi_data).to_excel(writer, sheet_name='Hindi', index=False)
                pd.DataFrame(english_data).to_excel(writer, sheet_name='English', index=False)
            output_paths.append(f"{base_path}.xlsx")
        
        # Create image ZIP if requested
        if self.options.get('save_images', False):
            zip_path = f"{base_path}_images.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for img in self.images:
                    zipf.write(img, os.path.basename(img))
            output_paths.append(zip_path)
        
        return output_paths

@celery.task(bind=True, name='process_pdf_task')
def process_pdf_task(self, pdf_type, file_urls, options):
    processor = PDFProcessor(pdf_type, file_urls, options)
    return processor.process()