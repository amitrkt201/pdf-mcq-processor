import re
from langdetect import detect, DetectorFactory

# Ensure consistent language detection
DetectorFactory.seed = 0

def separate_languages(text):
    hindi_lines = []
    english_lines = []
    hindi_chars = r'[\u0900-\u097F\uA8E0-\uA8FF]'  # Hindi Unicode ranges
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check for Hindi characters
        if re.search(hindi_chars, line):
            hindi_lines.append(line)
        else:
            # Fallback to langdetect for ambiguous lines
            try:
                if detect(line) == 'hi':
                    hindi_lines.append(line)
                else:
                    english_lines.append(line)
            except:
                english_lines.append(line)
                
    return '\n'.join(hindi_lines), '\n'.join(english_lines)

def detect_qa_structure(text, custom_words=''):
    patterns = {
        'question': r'(प्रश्न\d+:|Question\d+:|Q\d+\.|\?|प्र\.)',
        'option': r'(\([A-D]\)|[a-d]\)|\d+\.|\u0915|\u0916|\u0917|\u0918|Option)',
        'answer': r'(उत्तर|Answer|Ans\.?|Solution|सही उत्तर)',
        'explanation': r'(स्पष्टीकरण|Explanation|Reason|विवरण)'
    }
    
    # Add custom detection words
    if custom_words:
        custom_list = [word.strip() for word in custom_words.split(',') if word.strip()]
        patterns['question'] = f"({'|'.join(custom_list)})|{patterns['question']}"
    
    # Process text
    sections = {
        'question': '',
        'options': [],
        'answer': '',
        'explanation': ''
    }
    current_section = None
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if re.search(patterns['question'], line, re.IGNORECASE):
            current_section = 'question'
            sections['question'] = line
        elif re.search(patterns['option'], line):
            current_section = 'options'
            sections['options'].append(line)
        elif re.search(patterns['answer'], line):
            current_section = 'answer'
            sections['answer'] = line
        elif re.search(patterns['explanation'], line):
            current_section = 'explanation'
            sections['explanation'] = line
        elif current_section:
            if current_section == 'options':
                if sections['options']:
                    sections['options'][-1] += ' ' + line
            else:
                sections[current_section] += ' ' + line
                
    # Cleanup options
    sections['options'] = '\n'.join(sections['options'])
    
    return sections