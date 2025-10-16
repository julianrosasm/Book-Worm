import os
import json
import chromadb
from chromadb.config import Settings

def load_data_to_chromadb(data_path="app/data", collection_name="book_worm"):
    """
    Load all JSON chunks from the data directory into ChromaDB
    
    Args:
        data_path: Path to the data directory containing series folders
        collection_name: Name of the ChromaDB collection to create/use
    """
    # Initialize ChromaDB client
    # This creates a persistent database in the ./chroma_db folder
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Get or create collection
    # Using cosine similarity for semantic search
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    print(f"📊 Loading data into ChromaDB collection: {collection_name}")
    print(f"{'='*60}\n")
    
    total_chunks = 0
    documents = []
    metadatas = []
    ids = []
    
    # Walk through all series folders
    for series_name in os.listdir(data_path):
        series_path = os.path.join(data_path, series_name)
        
        if not os.path.isdir(series_path):
            continue
            
        print(f"📚 Processing series: {series_name}")
        
        # Walk through types (books, characters, etc.)
        for doc_type in os.listdir(series_path):
            type_path = os.path.join(series_path, doc_type)
            
            if not os.path.isdir(type_path):
                continue
            
            # Process each JSON file
            for filename in os.listdir(type_path):
                if not filename.endswith('.json'):
                    continue
                    
                filepath = os.path.join(type_path, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        chunks = json.load(f)
                    
                    # Add each chunk to the batch
                    for i, chunk in enumerate(chunks):
                        # Create unique ID for this chunk
                        chunk_id = f"{series_name}_{doc_type}_{filename.replace('.json', '')}_{i}"
                        
                        # Extract text content
                        text = chunk.get('text', '')
                        
                        # Prepare metadata (everything except the text)
                        metadata = {
                            'series': chunk.get('series', series_name),
                            'type': chunk.get('type', doc_type),
                            'name': chunk.get('name', ''),
                            'section': chunk.get('section', ''),
                        }
                        
                        # Add book_number and source_book if they exist
                        if 'book_number' in chunk and chunk['book_number'] is not None:
                            metadata['book_number'] = chunk['book_number']
                        
                        if 'source_book' in chunk and chunk['source_book'] is not None:
                            metadata['source_book'] = chunk['source_book']
                        
                        # Add to batches
                        documents.append(text)
                        metadatas.append(metadata)
                        ids.append(chunk_id)
                        total_chunks += 1
                    
                    print(f"  ✅ {filename}: {len(chunks)} chunks")
                    
                except Exception as e:
                    print(f"  ❌ Error loading {filename}: {e}")
        
        print()  # Empty line between series
    
    # Add all documents to ChromaDB in one batch
    if documents:
        print(f"\n{'='*60}")
        print(f"💾 Adding {total_chunks} chunks to ChromaDB...")
        
        # ChromaDB has a batch size limit, so we'll add in batches of 5000
        batch_size = 5000
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            collection.add(
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx]
            )
            print(f"  Added batch {i//batch_size + 1}: {end_idx}/{len(documents)} chunks")
        
        print(f"\n✅ Successfully loaded {total_chunks} chunks into ChromaDB!")
        print(f"{'='*60}\n")
    else:
        print("⚠️  No documents found to load")
    
    return collection


if __name__ == "__main__":
    # Load all data into ChromaDB
    collection = load_data_to_chromadb()
