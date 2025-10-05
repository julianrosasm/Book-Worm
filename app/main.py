import os
import requests
from bs4 import BeautifulSoup
import json
from collections import defaultdict

# Set the book series name here for general use
series_name = "RedRising"  # Change this to any book series name
data_path = f"app/data/{series_name}"
os.makedirs(data_path, exist_ok=True)

# List of URLs to process
urls = [
    {"url": "https://red-rising.fandom.com/wiki/Red_Rising_(Book_One)", "type": "books", "name": "Red Rising"},
    {"url": "https://red-rising.fandom.com/wiki/Golden_Son_(Book_Two)", "type": "books", "name": "Golden Son"},
    {"url": "https://red-rising.fandom.com/wiki/Morning_Star_(Book_Three)", "type": "books", "name": "Morning Star"},
    {"url": "https://red-rising.fandom.com/wiki/Iron_Gold_(Book_Four)", "type": "books", "name": "Iron Gold"},
    {"url": "https://red-rising.fandom.com/wiki/Dark_Age_(Book_Five)", "type": "books", "name": "Dark Age"},
    {"url": "https://red-rising.fandom.com/wiki/Light_Bringer_(Book_Six)", "type": "books", "name": "Light Bringer"},
    {"url": "https://red-rising.fandom.com/wiki/Darrow_O%27Lykos", "type": "characters", "name": "Darrow O'Lykos"}
]


def extract_sections_by_heading(html):
    soup = BeautifulSoup(html, "html.parser")
    current_heading = "General"
    chunks = []
    for elem in soup.find_all(['h2', 'h3', 'p']):
        if elem.name in ['h2', 'h3']:
            heading = elem.text.strip()
            if heading:
                current_heading = heading
        elif elem.name == 'p':
            text = elem.text.strip()
            if text:
                chunks.append({'text': text, 'section': current_heading})
    return chunks


def merge_chunks_by_section(chunks, name, doc_type, max_words=350, max_paragraphs=8):
    section_map = defaultdict(list)
    for chunk in chunks:
        section_map[chunk['section']].append(chunk['text'])

    merged = []
    for section, paragraphs in section_map.items():
        total_words = sum(len(p.split()) for p in paragraphs)
        # If section is short, keep as one chunk
        if total_words <= max_words and len(paragraphs) <= max_paragraphs:
            merged.append({
                'text': '\n\n'.join(paragraphs),
                'section': section,
                'name': name,
                'type': doc_type
            })
        else:
            # Otherwise, split as before
            buffer = []
            buffer_word_count = 0
            for para in paragraphs:
                word_count = len(para.split())
                if buffer and (len(buffer) >= max_paragraphs or buffer_word_count + word_count > max_words):
                    merged.append({
                        'text': '\n\n'.join(buffer),
                        'section': section,
                        'name': name,
                        'type': doc_type
                    })
                    buffer = []
                    buffer_word_count = 0
                buffer.append(para)
                buffer_word_count += word_count
            if buffer:
                merged.append({
                    'text': '\n\n'.join(buffer),
                    'section': section,
                    'name': name,
                    'type': doc_type
                })
    return merged


for entry in urls:
    url = entry["url"]
    doc_type = entry["type"]  # e.g., books, characters, events
    doc_name = entry["name"]  # e.g., "Red Rising", "Darrow O'Lykos"

    # Create subfolder for the type if it doesn't exist
    type_path = os.path.join(data_path, doc_type)
    os.makedirs(type_path, exist_ok=True)

    try:
        # Fetch the webpage
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses

        # Extract and tag sections by heading
        chunks = extract_sections_by_heading(response.text)
        merged_chunks = merge_chunks_by_section(chunks, doc_name, doc_type)

        # Save merged_chunks to a JSON file (one per document)
        safe_name = doc_name.replace("/", "-").replace("'", "")
        file_path = os.path.join(type_path, f"{safe_name}.json")
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(merged_chunks, file, indent=2, ensure_ascii=False)

        print(f"Saved: {file_path} ({len(merged_chunks)} chunks)")
    except Exception as e:
        print(f"Failed to process {url}: {e}")