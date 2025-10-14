import os
import requests
import json
from collections import defaultdict
import re

# ============================================
# SERIES CONFIGURATION
# Add your book series here!
# ============================================

SERIES_CONFIG = {
    "RedRising": {
        "wiki": "red-rising.fandom.com",
        "pages": [
            {"title": "Red_Rising_(Book_One)", "type": "books", "name": "Red Rising", "book_number": 1},
            {"title": "Golden_Son_(Book_Two)", "type": "books", "name": "Golden Son", "book_number": 2},
            {"title": "Morning_Star_(Book_Three)", "type": "books", "name": "Morning Star", "book_number": 3},
            {"title": "Iron_Gold_(Book_Four)", "type": "books", "name": "Iron Gold", "book_number": 4},
            {"title": "Dark_Age_(Book_Five)", "type": "books", "name": "Dark Age", "book_number": 5},
            {"title": "Light_Bringer_(Book_Six)", "type": "books", "name": "Light Bringer", "book_number": 6},
            {"title": "Darrow_O'Lykos", "type": "characters", "name": "Darrow O'Lykos", "book_number": None}
        ],
        "book_names": ["Red Rising", "Golden Son", "Morning Star", "Iron Gold", "Dark Age", "Light Bringer"]
    },
    
    "HarryPotter": {
        "wiki": "harrypotter.fandom.com",
        "pages": [
            {"title": "Harry_Potter_and_the_Philosopher's_Stone", "type": "books", "name": "Philosopher's Stone", "book_number": 1},
            {"title": "Harry_Potter_and_the_Chamber_of_Secrets", "type": "books", "name": "Chamber of Secrets", "book_number": 2},
            {"title": "Harry_Potter_and_the_Prisoner_of_Azkaban", "type": "books", "name": "Prisoner of Azkaban", "book_number": 3},
            {"title": "Harry_Potter_and_the_Goblet_of_Fire", "type": "books", "name": "Goblet of Fire", "book_number": 4},
            {"title": "Harry_Potter_and_the_Order_of_the_Phoenix", "type": "books", "name": "Order of the Phoenix", "book_number": 5},
            {"title": "Harry_Potter_and_the_Half-Blood_Prince", "type": "books", "name": "Half-Blood Prince", "book_number": 6},
            {"title": "Harry_Potter_and_the_Deathly_Hallows", "type": "books", "name": "Deathly Hallows", "book_number": 7},
            {"title": "Harry_Potter", "type": "characters", "name": "Harry Potter", "book_number": None},
            {"title": "Hermione_Granger", "type": "characters", "name": "Hermione Granger", "book_number": None},
            {"title": "Ron_Weasley", "type": "characters", "name": "Ron Weasley", "book_number": None},
        ],
        "book_names": ["Philosopher's Stone", "Chamber of Secrets", "Prisoner of Azkaban", "Goblet of Fire", "Order of the Phoenix", "Half-Blood Prince", "Deathly Hallows"]
    }
}


def get_page_content(page_title, api_url):
    """Fetch page content using Fandom's MediaWiki API"""
    params = {
        'action': 'parse',
        'page': page_title,
        'prop': 'wikitext',
        'format': 'json'
    }
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'parse' in data and 'wikitext' in data['parse']:
            return data['parse']['wikitext']['*']
        else:
            print(f"No content found for {page_title}")
            return None
    except Exception as e:
        print(f"Error fetching {page_title}: {e}")
        return None


def parse_wikitext_sections(wikitext):
    """Parse wikitext and extract sections with their content"""
    if not wikitext:
        return []
    
    # Split by section headers (== Header ==)
    sections = []
    current_section = "General"
    current_content = []
    
    lines = wikitext.split('\n')
    
    for line in lines:
        # Check for section headers
        header_match = re.match(r'^(==+)\s*(.+?)\s*\1$', line)
        if header_match:
            # Save previous section if it has content
            if current_content:
                text = '\n'.join(current_content).strip()
                # Remove wiki markup
                text = clean_wikitext(text)
                if text:
                    sections.append({
                        'text': text,
                        'section': current_section
                    })
            
            # Start new section - clean the section name too
            current_section = clean_wikitext(header_match.group(2).strip())
            current_content = []
        else:
            # Add content to current section
            current_content.append(line)
    
    # Don't forget the last section
    if current_content:
        text = '\n'.join(current_content).strip()
        text = clean_wikitext(text)
        if text:
            sections.append({
                'text': text,
                'section': current_section
            })
    
    return sections


def clean_wikitext(text):
    """Remove wiki markup from text"""
    # Remove templates {{...}}
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    
    # Remove file/image references
    text = re.sub(r'\[\[File:.*?\]\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[\[Image:.*?\]\]', '', text, flags=re.IGNORECASE)
    
    # Convert wiki links [[Link|Text]] to Text, or [[Link]] to Link
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)
    
    # Remove external links markup
    text = re.sub(r'\[https?://[^\s\]]+ ([^\]]+)\]', r'\1', text)
    text = re.sub(r'\[https?://[^\s\]]+\]', '', text)
    
    # Remove bold/italic markup
    text = re.sub(r"'''([^']+)'''", r'\1', text)
    text = re.sub(r"''([^']+)''", r'\1', text)
    
    # Remove references <ref>...</ref>
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^>]*\/>', '', text)
    
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # Remove ALL HTML tags (including <u>, <b>, <i>, <s>, etc.) but keep their content
    text = re.sub(r'</?[^>]+>', '', text)
    
    # Clean up excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()


def detect_book_from_section(section_name, book_names):
    """Detect which book a character section belongs to based on section name"""
    # Map of book titles to book numbers (dynamically built from book_names)
    book_mapping = {name: idx + 1 for idx, name in enumerate(book_names)}
    
    # Check if any book name is in the section
    for book_name, book_num in book_mapping.items():
        if book_name in section_name:
            return book_num, book_name
    
    # If no specific book found, return None
    return None, None


def merge_chunks_by_section(chunks, name, doc_type, series_name, book_names, book_number=None, max_words=400, max_paragraphs=4, hard_max_words=600):
    """
    Merge chunks by section with intelligent splitting
    
    Args:
        max_words: Target maximum words per chunk
        max_paragraphs: Maximum paragraphs per chunk
        hard_max_words: Absolute maximum - will force split even single paragraphs
    """
    section_map = defaultdict(list)
    for chunk in chunks:
        section_map[chunk['section']].append(chunk['text'])

    merged = []
    for section, paragraphs in section_map.items():
        total_words = sum(len(p.split()) for p in paragraphs)
        
        # For character chunks, try to detect which book the section is from
        section_book_num = book_number
        section_source_book = name if book_number else None
        
        if doc_type == 'characters':
            detected_num, detected_book = detect_book_from_section(section, book_names)
            if detected_num:
                section_book_num = detected_num
                section_source_book = detected_book
        
        # If section is short, keep as one chunk
        if total_words <= max_words and len(paragraphs) <= max_paragraphs:
            chunk_data = {
                'text': '\n\n'.join(paragraphs),
                'section': section,
                'name': name,
                'type': doc_type,
                'series': series_name
            }
            if section_book_num is not None:
                chunk_data['book_number'] = section_book_num
                chunk_data['source_book'] = section_source_book
            merged.append(chunk_data)
        else:
            # Otherwise, split intelligently
            buffer = []
            buffer_word_count = 0
            for para in paragraphs:
                para_word_count = len(para.split())
                
                # Check if this single paragraph is too long
                if para_word_count > hard_max_words:
                    # Save current buffer first
                    if buffer:
                        chunk_data = {
                            'text': '\n\n'.join(buffer),
                            'section': section,
                            'name': name,
                            'type': doc_type,
                            'series': series_name
                        }
                        if section_book_num is not None:
                            chunk_data['book_number'] = section_book_num
                            chunk_data['source_book'] = section_source_book
                        merged.append(chunk_data)
                        buffer = []
                        buffer_word_count = 0
                    
                    # Split the long paragraph by sentences using better regex
                    # Match sentence endings: . ! ? followed by space or end of string
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    sent_buffer = []
                    sent_word_count = 0
                    
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence:
                            continue
                        sent_words = len(sentence.split())
                        
                        # If single sentence is still too long, force split by words
                        if sent_words > max_words:
                            words = sentence.split()
                            for i in range(0, len(words), max_words):
                                chunk_text = ' '.join(words[i:i+max_words])
                                chunk_data = {
                                    'text': chunk_text,
                                    'section': section,
                                    'name': name,
                                    'type': doc_type,
                                    'series': series_name
                                }
                                if section_book_num is not None:
                                    chunk_data['book_number'] = section_book_num
                                    chunk_data['source_book'] = section_source_book
                                merged.append(chunk_data)
                            continue
                        
                        if sent_buffer and (sent_word_count + sent_words > max_words):
                            # Save sentence buffer
                            chunk_data = {
                                'text': ' '.join(sent_buffer),
                                'section': section,
                                'name': name,
                                'type': doc_type,
                                'series': series_name
                            }
                            if section_book_num is not None:
                                chunk_data['book_number'] = section_book_num
                                chunk_data['source_book'] = section_source_book
                            merged.append(chunk_data)
                            sent_buffer = []
                            sent_word_count = 0
                        
                        sent_buffer.append(sentence)
                        sent_word_count += sent_words
                    
                    # Save remaining sentences
                    if sent_buffer:
                        chunk_data = {
                            'text': ' '.join(sent_buffer),
                            'section': section,
                            'name': name,
                            'type': doc_type,
                            'series': series_name
                        }
                        if section_book_num is not None:
                            chunk_data['book_number'] = section_book_num
                            chunk_data['source_book'] = section_source_book
                        merged.append(chunk_data)
                    continue
                
                # Normal paragraph handling
                if buffer and (len(buffer) >= max_paragraphs or buffer_word_count + para_word_count > max_words):
                    chunk_data = {
                        'text': '\n\n'.join(buffer),
                        'section': section,
                        'name': name,
                        'type': doc_type,
                        'series': series_name
                    }
                    if section_book_num is not None:
                        chunk_data['book_number'] = section_book_num
                        chunk_data['source_book'] = section_source_book
                    merged.append(chunk_data)
                    buffer = []
                    buffer_word_count = 0
                buffer.append(para)
                buffer_word_count += para_word_count
            if buffer:
                chunk_data = {
                    'text': '\n\n'.join(buffer),
                    'section': section,
                    'name': name,
                    'type': doc_type,
                    'series': series_name
                }
                if section_book_num is not None:
                    chunk_data['book_number'] = section_book_num
                    chunk_data['source_book'] = section_source_book
                merged.append(chunk_data)
    return merged


# ============================================
# MAIN PROCESSING LOOP
# ============================================

# Process each series in the configuration
for series_name, series_config in SERIES_CONFIG.items():
    print(f"\n{'='*60}")
    print(f"📚 Processing series: {series_name}")
    print(f"{'='*60}")
    
    # Setup paths and API for this series
    data_path = f"app/data/{series_name}"
    os.makedirs(data_path, exist_ok=True)
    
    wiki_base = series_config["wiki"]
    api_url = f"https://{wiki_base}/api.php"
    pages = series_config["pages"]
    book_names = series_config["book_names"]
    
    # Process each page in the series
    for entry in pages:
        page_title = entry["title"]
        doc_type = entry["type"]  # e.g., books, characters, events
        doc_name = entry["name"]  # e.g., "Red Rising", "Darrow O'Lykos"
        book_number = entry.get("book_number")  # Get book number if available

        # Create subfolder for the type if it doesn't exist
        type_path = os.path.join(data_path, doc_type)
        os.makedirs(type_path, exist_ok=True)

        try:
            # Fetch page content using Fandom API
            wikitext = get_page_content(page_title, api_url)
            
            if not wikitext:
                print(f"⚠️  Skipping {page_title} - no content available")
                continue
            
            # Parse wikitext into sections
            chunks = parse_wikitext_sections(wikitext)
            merged_chunks = merge_chunks_by_section(chunks, doc_name, doc_type, series_name, book_names, book_number)

            # Save merged_chunks to a JSON file (one per document)
            safe_name = doc_name.replace("/", "-").replace("'", "")
            file_path = os.path.join(type_path, f"{safe_name}.json")
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(merged_chunks, file, indent=2, ensure_ascii=False)

            print(f"✅ Saved: {file_path} ({len(merged_chunks)} chunks)")
        except Exception as e:
            print(f"❌ Failed to process {page_title}: {e}")

print(f"\n{'='*60}")
print(f"🎉 All series processed successfully!")
print(f"{'='*60}\n")