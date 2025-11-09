import chromadb
import sys
from sentence_transformers import SentenceTransformer

def query_books(query_text, series_filter=None, max_book_number=None, n_results=15):
    """
    Query the Book-Worm vector database
    
    Args:
        query_text: Your question or search query
        series_filter: Optional - filter by series name (e.g., "RedRising", "Mistborn")
        max_book_number: Optional - prevent spoilers by only showing books up to this number
        n_results: Number of results to return
    """
    # Connect to the existing ChromaDB database
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="book_worm")
    
    # Load the same embedding model used in the database
    model = SentenceTransformer('all-mpnet-base-v2')
    
    # Build filter clause
    where_clause = None
    filters = []
    
    if series_filter:
        filters.append({"series": series_filter})
    
    if max_book_number is not None:
        # Only show chunks from books <= max_book_number
        # Chunks without book_number will be excluded (correct behavior for spoiler prevention)
        filters.append({"book_number": {"$lte": max_book_number}})
    
    if len(filters) == 1:
        where_clause = filters[0]
    elif len(filters) > 1:
        where_clause = {"$and": filters}
    
    # Query using the proper embedding model
    print(f"\n{'='*80}")
    print(f"🔍 QUERY: {query_text}")
    if series_filter:
        print(f"📚 Series filter: {series_filter}")
    if max_book_number:
        print(f"📖 Spoiler protection: Only showing books 1-{max_book_number}")
    print(f"{'='*80}\n")
    
    # Use the same embedding model as the database
    query_embedding = model.encode([query_text])
    
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=n_results,
        where=where_clause
    )
    
    # Display results
    if not results['documents'][0]:
        print("❌ No results found")
        return
    
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        similarity = (1 - distance) * 100
        print(f"{'─'*80}")
        print(f"📄 RESULT #{i+1} - Similarity: {similarity:.1f}%")
        print(f"{'─'*80}")
        print(f"Series:  {metadata.get('series', 'N/A')}")
        print(f"Type:    {metadata.get('type', 'N/A')}")
        print(f"Name:    {metadata.get('name', 'N/A')}")
        print(f"Section: {metadata.get('section', 'N/A')}")
        
        if 'book_number' in metadata and metadata['book_number'] is not None:
            print(f"Book:    #{metadata['book_number']} - {metadata.get('source_book', 'N/A')}")
        
        print(f"\n{doc}\n")
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        # Command-line query
        query = " ".join(sys.argv[1:])
        query_books(query)
    else:
        # Interactive mode
        print("="*80)
        print("📚 BOOK-WORM RAG - Interactive Query Tool")
        print("="*80)
        print("\nExamples:")
        print("  • Who is Darrow?")
        print("  • What are Vin's abilities?")
        print("  • How does allomancy work?")
        print("\nType 'quit' to exit\n")
        
        while True:
            try:
                query = input("🔍 Your question: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!\n")
                    break
                
                if not query:
                    continue
                
                # Ask about filters
                series = input("📚 Filter by series? (press Enter to skip): ").strip()
                series = series if series else None
                
                book_num = input("📖 Max book number for spoiler protection? (press Enter to skip): ").strip()
                book_num = int(book_num) if book_num.isdigit() else None
                
                # Run query
                query_books(query, series_filter=series, max_book_number=book_num)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
