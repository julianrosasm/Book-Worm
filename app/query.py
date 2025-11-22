import chromadb
import sys
from sentence_transformers import SentenceTransformer

def query_books(query_text, series_filter=None, max_book_number=None, n_results=15):
    """
    Query the Book-Worm vector database
    
    Args:
        query_text: Your question or search query
        series_filter: Optional - filter by series name (e.g., "Red Rising", "Harry Potter")
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
    
    if len(filters) == 1:
        where_clause = filters[0]
    elif len(filters) > 1:
        where_clause = {"$and": filters}
    
    # Query using the proper embedding model
    print(f"\n{'='*80}")
    print(f"QUERY: {query_text}")
    if series_filter:
        print(f"Series filter: {series_filter}")
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
        print(f"RESULT #{i+1} - Similarity: {similarity:.1f}%")
        print(f"{'─'*80}")
        print(f"Series:  {metadata.get('series', 'N/A')}")
        print(f"Type:    {metadata.get('type', 'N/A')}")
        print(f"Name:    {metadata.get('name', 'N/A')}")
        print(f"Section: {metadata.get('section', 'N/A')}")
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
        print("BOOK-WORM RAG - Interactive Query")
        print("="*80)
        print("\nExamples:")
        print("  • Who is Darrow?")
        print("  • What happens at the Institute?")
        print("  • Who is Ron Weasley?")
        print("\nType 'quit' to exit\n")
        
        while True:
            try:
                query = input("Your question: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!\n")
                    break
                
                if not query:
                    continue
                
                # Ask about filters
                series = input("Filter by series? (press Enter to skip): ").strip()
                series = series if series else None
                
                # Run query
                query_books(query, series_filter=series)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
