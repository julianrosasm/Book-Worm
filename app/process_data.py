import os
import requests
import json
from collections import defaultdict
import re

# ============================================
# LOAD SERIES CONFIGURATION FROM EXTERNAL FILE
# Edit series_config.json to add new series!
# ============================================

def load_series_config():
    """Load series configuration from external JSON file"""
    config_path = "app/series_config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {config_path} not found!")
        print("Please create series_config.json with your series data.")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {config_path}: {e}")
        return {}

SERIES_CONFIG = load_series_config()


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
            wikitext = data['parse']['wikitext']['*']
            # Check for redirect
            redirect_match = re.match(r'#REDIRECT\s+\[\[(.+?)\]\]', wikitext, re.IGNORECASE)
            if redirect_match:
                target_title = redirect_match.group(1)
                # Recursively fetch the target page
                return get_page_content(target_title, api_url)
            return wikitext
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


def merge_chunks_by_section(chunks, name, doc_type, series_name, max_words=400):
    section_map = defaultdict(list)
    for chunk in chunks:
        section_map[chunk['section']].append(chunk['text'])

    merged = []
    for section, paragraphs in section_map.items():
        block = '\n\n'.join(paragraphs)
        words = block.split()
        for i in range(0, len(words), max_words):
            chunk_text = ' '.join(words[i:i+max_words])
            chunk_data = {
                'text': chunk_text,
                'section': section,
                'name': name,
                'type': doc_type,
                'series': series_name
            }
            merged.append(chunk_data)
    return merged


# ============================================
# MAIN PROCESSING LOOP
# ============================================

if not SERIES_CONFIG:
    print("❌ No series configuration loaded. Exiting.")
    exit(1)

# Process each series in the configuration
for series_name, series_config in SERIES_CONFIG.items():
    print(f"\n{'='*60}")
    print(f"Processing series: {series_name}")
    print(f"{'='*60}")
    
    # Setup paths and API for this series
    data_path = f"app/data/{series_name}"
    os.makedirs(data_path, exist_ok=True)
    
    wiki_base = series_config["wiki"]
    api_url = f"https://{wiki_base}/api.php"
    pages = series_config["pages"]
    
    # Process each page in the series
    for entry in pages:
        page_title = entry["title"]
        doc_type = entry["type"]  # e.g., characters, events
        doc_name = entry["name"]  # e.g., "Darrow O'Lykos", "The Institute"

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
            merged_chunks = merge_chunks_by_section(chunks, doc_name, doc_type, series_name)

            # Save merged_chunks to a JSON file (one per document)
            safe_name = doc_name.replace("/", "-").replace("'", "")
            file_path = os.path.join(type_path, f"{safe_name}.json")
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(merged_chunks, file, indent=2, ensure_ascii=False)

            print(f"✅ Saved: {file_path} ({len(merged_chunks)} chunks)")
        except Exception as e:
            print(f"❌ Failed to process {page_title}: {e}")

print(f"\n{'='*60}")
print(f"All series processed successfully!")
print(f"{'='*60}\n")