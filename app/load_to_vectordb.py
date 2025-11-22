import os
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from chromadb import Documents, EmbeddingFunction, Embeddings

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
    
    # Delete existing collection if it exists for fresh start
    try:
        client.delete_collection(name=collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except ValueError as e:
        if "does not exist" in str(e).lower():
            print(f"Collection '{collection_name}' doesn't exist yet (first run)")
        else:
            print(f"⚠️  Error deleting collection: {e}")
    except Exception as e:
        print(f"⚠️  Error deleting collection: {e}")
    
    # Force cleanup of old data
    print("Forcing cleanup of old vector database files...")
    import shutil
    import os
    
    # Remove old chroma folders
    chroma_path = "./chroma_db"
    if os.path.exists(chroma_path):
        for item in os.listdir(chroma_path):
            item_path = os.path.join(chroma_path, item)
            if os.path.isdir(item_path) and len(item) == 36:  # UUID folders
                try:
                    shutil.rmtree(item_path)
                    print(f"Removed old database folder: {item}")
                except Exception as e:
                    print(f"⚠️  Could not remove {item}: {e}")
    
    # Recreate client to ensure clean state
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Load high-quality embedding model
    print("Loading embedding model...")
    model = SentenceTransformer('all-mpnet-base-v2')
    print("✅ Model loaded: all-mpnet-base-v2 (768 dimensions)")
    
    # Create collection with custom embedding function
    class CustomEmbeddingFunction(EmbeddingFunction):
        def __call__(self, input: Documents) -> Embeddings:
            return model.encode(input).tolist()
    
    # Get or create collection
    # Using cosine similarity for semantic search
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=CustomEmbeddingFunction()
    )
    
    print(f"Loading data into ChromaDB collection: {collection_name}")
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
            
        print(f"Processing series: {series_name}")
        
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
                        
                        # Extract text content and enhance it for better search
                        text = chunk.get('text', '')
                        
                        # Add contextual information for better semantic understanding
                        enhanced_text = text
                        section = chunk.get('section', '')
                        name = chunk.get('name', '')
                        series = chunk.get('series', series_name)
                        doc_type_clean = chunk.get('type', doc_type)
                        
                        # Add context parts to help with search
                        context_parts = []
                        if section and section != 'General':
                            context_parts.append(f"Section: {section}")
                        if name:
                            context_parts.append(f"About: {name}")
                        if doc_type_clean:
                            context_parts.append(f"Type: {doc_type_clean}")
                        if series:
                            context_parts.append(f"Series: {series}")
                        
                        if context_parts:
                            enhanced_text = f"{' | '.join(context_parts)}\n\n{text}"
                        
                        # Prepare metadata (everything except the text)
                        metadata = {
                            'series': chunk.get('series', series_name),
                            'type': chunk.get('type', doc_type),
                            'name': chunk.get('name', ''),
                            'section': chunk.get('section', ''),
                        }
                        
                        # Add to batches
                        documents.append(enhanced_text)
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
        print(f"Adding {total_chunks} chunks to ChromaDB...")
        
        # ChromaDB has a batch size limit, so we'll add in batches
        batch_size = 100  # Smaller batches for custom embedding function
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            print(f"  Processing batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}...")
            
            collection.add(
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx]
            )
        
        print(f"\n✅ Successfully loaded {total_chunks} chunks into ChromaDB")
        print(f"{'='*60}")

    else:
        print("⚠️  No documents found to load")
    
    return collection


if __name__ == "__main__":
    # Load all data into ChromaDB
    collection = load_data_to_chromadb()
