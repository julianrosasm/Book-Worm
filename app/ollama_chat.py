import requests
import sys
sys.path.append('.')

from query import query_books
import chromadb
from sentence_transformers import SentenceTransformer

class BookWormOllamaRAG:
    """RAG system using Ollama for local LLM inference"""
    
    def __init__(self, model_name="llama3.2:latest", ollama_url="http://localhost:11434"):
        """
        Initialize BookWorm RAG with Ollama
        
        Args:
            model_name: Ollama model to use (llama3.2:latest)
            ollama_url: URL where Ollama is running
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        
        # Initialize ChromaDB connection
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_collection(name="book_worm")
        
        # Load the same embedding model used in the database
        self.model = SentenceTransformer('all-mpnet-base-v2')
        
        # Test Ollama connection
        self.ollama_ready = self.testConnection()
        if not self.ollama_ready:
            print("\n  Ollama is not ready. You can still search your books, but AI responses won't work.")
            print(" To fix: Make sure Ollama is running with: ollama serve")
            print(" Or try restarting the Ollama app\n")
    
    def testConnection(self):
        """Test if Ollama is running and model is available"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = [model['name'] for model in response.json().get('models', [])]
                if self.model_name in models:
                    print(f" Ollama connected with model: {self.model_name}")
                    
                    # Test with a simple prompt
                    print(" Testing model response...")
                    test_response = self.callOllama("Say 'Hello' in one word.", max_tokens=10)
                    if "Error:" not in test_response:
                        print(" Model test successful!")
                        return True
                    else:
                        print(f" Model test failed: {test_response}")
                        return False
                else:
                    print(f"  Model {self.model_name} not found. Available models: {models}")
                    print(" You can pull a model with: ollama pull llama3.2")
                    return False
            else:
                print(f" Ollama not responding. Status: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(" Cannot connect to Ollama. Is it running?")
            print(" Start Ollama with: ollama serve")
            return False
        except Exception as e:
            print(f" Ollama connection error: {e}")
            return False
    
    def getRelevantContext(self, query, series_filter=None, book_filter=None, max_book_number=None, n_results=15):
        """Retrieve relevant context from ChromaDB"""
        
        # Build filter
        where_clause = None
        filters = []
        
        if series_filter:
            filters.append({"series": series_filter})
        if book_filter:
            # Filter by book name (matches source_book or name field)
            book_filters = [
                {"source_book": {"$eq": book_filter}},
                {"name": {"$eq": book_filter}}
            ]
            filters.append({"$or": book_filters})
        if max_book_number is not None:
            filters.append({"book_number": {"$lte": max_book_number}})
        
        if len(filters) == 1:
            where_clause = filters[0]
        elif len(filters) > 1:
            where_clause = {"$and": filters}
        
        # Query ChromaDB using the proper embedding model
        query_embedding = self.model.encode([query])
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            where=where_clause
        )
        
        # Format results
        context_chunks = []
        for doc, metadata, distance in zip(
            results['documents'][0], 
            results['metadatas'][0], 
            results['distances'][0]
        ):
            similarity = (1 - distance) * 100
            
            context_chunks.append({
                'text': doc,
                'series': metadata.get('series', ''),
                'type': metadata.get('type', ''),
                'name': metadata.get('name', ''),
                'section': metadata.get('section', ''),
                'book_number': metadata.get('book_number'),
                'source_book': metadata.get('source_book', ''),
                'similarity': similarity
            })
        
        return context_chunks
    
    def formatContext(self, context_chunks):
        """Format context chunks into a prompt for the LLM"""
        if not context_chunks:
            return "No relevant information found in the books."
        
        context = "RELEVANT INFORMATION FROM BOOKS:\n\n"
        
        for i, chunk in enumerate(context_chunks, 1):
            # Build source info
            source = f"{chunk['series']}"
            if chunk['book_number']:
                source += f" - Book {chunk['book_number']}"
            if chunk['source_book']:
                source += f" ({chunk['source_book']})"
            if chunk['name']:
                source += f" - {chunk['name']}"
            if chunk['section']:
                source += f" - {chunk['section']}"
            
            context += f"[Source {i}] {source} (Relevance: {chunk['similarity']:.1f}%)\n"
            context += f"{chunk['text']}\n\n"
        
        return context
    
    def callOllama(self, prompt, temperature=0.7, max_tokens=1000):
        """Make a request to Ollama API"""
        
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            print(" Thinking... (this may take 10-30 seconds)")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=data,
                timeout=120  # Increased timeout to 2 minutes
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response generated")
            else:
                return f"Error: Ollama returned status {response.status_code}\nResponse: {response.text}"
                
        except requests.exceptions.Timeout:
            return "Error: Request to Ollama timed out after 2 minutes. Try a shorter question or restart Ollama with: ollama serve"
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Make sure it's running with: ollama serve"
        except Exception as e:
            return f"Error calling Ollama: {e}"
    
    def ask(self, question, series_filter=None, book_filter=None, max_book_number=None, 
            show_context=False, n_results=15):
        """
        Ask a question about your books and get an AI-generated response
        
        Args:
            question: Your question about the books
            series_filter: Filter by series (e.g., "HarryPotter", "RedRising")
            book_filter: Filter by specific book (e.g., "Light Bringer", "Philosopher's Stone")
            max_book_number: Prevent spoilers by limiting to books 1-N
            show_context: Whether to show the retrieved context
            n_results: Number of context chunks to retrieve
        
        Returns:
            AI-generated answer based on book content
        """
        
        print(f"\n{'='*80}")
        print(f"BOOK-WORM AI CHAT")
        print(f"{'='*80}")
        print(f"Question: {question}")
        
        if series_filter:
            print(f" Series filter: {series_filter}")
        if book_filter:
            print(f" Book filter: {book_filter}")
        if max_book_number:
            print(f" Spoiler protection: Books 1-{max_book_number} only")
        
        print(f"\n Searching for relevant information...")
        
        # Get relevant context
        context_chunks = self.getRelevantContext(
            question, series_filter, book_filter, max_book_number, n_results
        )
        
        if not context_chunks:
            print(" No relevant information found in the books.")
            return "I couldn't find any relevant information about that in the books."
        
        print(f" Found {len(context_chunks)} relevant passages")
        
        # Show context if requested
        if show_context:
            print(f"\n RETRIEVED CONTEXT:")
            print("-" * 60)
            for chunk in context_chunks:
                source = f"{chunk['series']}"
                if chunk['book_number']:
                    source += f" - Book {chunk['book_number']}"
                if chunk['source_book']:
                    source += f" ({chunk['source_book']})"
                print(f"• {source} (Relevance: {chunk['similarity']:.1f}%)")
                print(f"  {chunk['text'][:100]}...")
                print()
        
        # Format context for LLM
        context = self.formatContext(context_chunks)
        
        # Create prompt
        prompt = f"""You are a knowledgeable book assistant helping someone understand books they've read. 
                    
                    {context}
                    
                    Based on the information above, please answer this question: {question}

                    Guidelines:
                        - Answer based only on the provided book information
                        - Be conversational, helpful, and engaging
                        - Mention which book or character the information comes from when relevant
                        - If the information is incomplete, acknowledge what you don't know
                        - Keep your answer focused and avoid unnecessary spoilers
                        - Write in a natural, friendly tone

                    Answer:"""

        print(f" Generating response with {self.model_name}...")
        
        # Check if Ollama is ready
        if not self.ollama_ready:
            print("\n  Ollama is not ready. Showing search results only.")
            return "Ollama is not available. Please check the search results above."
        
        # Get response from Ollama
        response = self.callOllama(prompt)
        
        print(f"\n AI RESPONSE:")
        print("-" * 60)
        print(response)
        print(f"\n{'='*80}\n")
        
        return response
    
    def chatMode(self):
        """Interactive chat mode"""
        print("=" * 80)
        print(" BOOK-WORM AI CHAT BOT")
        print("=" * 80)
        print("Ask me anything about your books!")
        print("\nCommands:")
        print("  • Type your question normally")
        print("  • Use /series <name> to filter by series")
        print("  • Use /book <title> to filter by specific book")
        print("  • Use /books <number> to limit spoilers")
        print("  • Use /context to show retrieved passages")
        print("  • Use /clear to reset all filters")
        print("  • Type 'quit' or 'exit' to leave")
        print()
        
        series_filter = None
        book_filter = None
        max_book_number = None
        show_context = False
        
        while True:
            try:
                user_input = input(" Ask about your books: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n Happy reading!\n")
                    break
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if user_input.startswith('/series '):
                        series_filter = user_input[8:].strip()
                        print(f" Series filter set to: {series_filter}")
                        continue
                    elif user_input.startswith('/book '):
                        book_filter = user_input[6:].strip()
                        print(f" Book filter set to: {book_filter}")
                        continue
                    elif user_input.startswith('/books '):
                        try:
                            max_book_number = int(user_input[7:].strip())
                            print(f" Spoiler protection: Books 1-{max_book_number}")
                            continue
                        except ValueError:
                            print(" Invalid book number")
                            continue
                    elif user_input == '/context':
                        show_context = not show_context
                        print(f" Show context: {'ON' if show_context else 'OFF'}")
                        continue
                    elif user_input == '/clear':
                        series_filter = None
                        book_filter = None
                        max_book_number = None
                        show_context = False
                        print(" Filters cleared")
                        continue
                    else:
                        print(" Unknown command")
                        continue
                
                # Process question
                self.ask(user_input, series_filter, book_filter, max_book_number, show_context)
                
            except KeyboardInterrupt:
                print("\n\n Happy reading!\n")
                break
            except Exception as e:
                print(f"\n Error: {e}\n")


def main():
    """Main function for the RAG system"""
    
    # Initialize the RAG system
    rag = BookWormOllamaRAG(model_name="llama3.2:latest")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Check for flags
        series_filter = None
        book_filter = None
        max_book_number = None
        show_context = True
        question_parts = []
        
        i = 1
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--series" and i + 1 < len(sys.argv):
                series_filter = sys.argv[i + 1]
                i += 2
            elif arg == "--book" and i + 1 < len(sys.argv):
                book_filter = sys.argv[i + 1]
                i += 2
            elif arg == "--books" and i + 1 < len(sys.argv):
                try:
                    max_book_number = int(sys.argv[i + 1])
                    i += 2
                except ValueError:
                    print(f" Invalid book number: {sys.argv[i + 1]}")
                    return
            elif arg == "--no-context":
                show_context = False
                i += 1
            else:
                question_parts.append(arg)
                i += 1
        
        if question_parts:
            question = " ".join(question_parts)
            rag.ask(question, series_filter=series_filter, book_filter=book_filter, max_book_number=max_book_number, show_context=show_context)
        else:
            print(" No question provided")
            print("\nUsage examples:")
            print('  python3 app/ollama_chat.py "Who is Harry Potter?"')
            print('  python3 app/ollama_chat.py --series RedRising "Tell me about Darrow"')
            print('  python3 app/ollama_chat.py --book "Light Bringer" "What happens at the end?"')
    else:
        # Start interactive chat mode
        rag.chatMode()


if __name__ == "__main__":
    main()
