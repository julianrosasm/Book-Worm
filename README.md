# BookWorm 📚

A Retrieval-Augmented Generation (RAG) system that lets you chat with your favorite book series using AI. Ask questions about characters, plot points, and get intelligent answers with spoiler protection!

## 🌟 Features

- **AI-Powered Chat**: Interactive conversations about your books using local Ollama models
- **Spoiler Protection**: Only get information from books you've read
- **Multi-Series Support**: Harry Potter, Red Rising, and easy expansion to new series
- **Book Filtering**: Focus conversations on specific books or series
- **Vector Search**: Semantic search through 769+ Fandom book overviews and character information
- **Local & Private**: All processing happens locally - your reading data stays private

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Ollama** (for AI chat functionality)

### 1. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from: https://ollama.ai/download
```

### 2. Pull the AI Model

```bash
ollama pull llama3.2:latest
```

### 3. Clone and Setup

```bash
git clone https://github.com/julianrosasm/Book-Worm.git
cd Book-Worm
pip install -r app/requirements.txt
```

### 4. Start Chatting!

```bash
# Start Ollama (if not already running)
ollama serve

# Launch BookWorm Chat
python3 app/ollama_chat.py
```

## 💬 How to Use

### Basic Chat

```
You: Tell me about Darrow's character development
AI: Darrow undergoes significant transformation throughout the Red Rising series...
```

### Book-Specific Questions

```
You: /book Light Bringer
You: What happens in the ending?
AI: [Focuses only on Light Bringer content]
```

### Series Filtering

```
You: /book HarryPotter
You: Compare Harry and Hermione's friendship
AI: [Only uses Harry Potter series information]
```

### Available Commands

- `/book <book_name>` - Filter to specific book
- `/series <series_name>` - Filter to specific series
- `/help` - Show all commands
- `/quit` - Exit chat

## 📁 Project Structure

```
Book-Worm/
├── README.md
├── app/
│   ├── requirements.txt      # Python dependencies
│   ├── ollama_chat.py       # Main chat interface
│   ├── query.py             # Vector search functionality
│   ├── process_data.py      # Data processing scripts
│   ├── load_to_vectordb.py  # ChromaDB setup
│   └── data/                # Book content (JSON format)
│       ├── HarryPotter/
│       │   ├── books/       # Plot summaries
│       │   └── characters/  # Character information
│       └── RedRising/
│           ├── books/
│           └── characters/
└── chroma_db/               # Vector database
    └── chroma.sqlite3       # Persistent storage
```

## 🛠️ Installation Details

### Python Dependencies

```bash
cd app
pip install -r requirements.txt
```

**Required packages:**

- `chromadb` - Vector database for semantic search
- `langchain` - Text processing utilities
- `requests` - HTTP client for Ollama API
- `markdownify` - Wiki content processing

### Verify Installation

```python
# Test ChromaDB connection
python3 -c "import chromadb; print('ChromaDB: OK')"

# Test Ollama connection
curl http://localhost:11434/api/tags
```

## 🔧 Configuration

### Ollama Settings

Default model: `llama3.2:latest` (4.1GB)

To use a different model:

```python
# In ollama_chat.py
BookWormOllamaRAG(model_name="llama3.1:latest")
```

### Model

- `llama3.2:latest` (recommended, 4GB)

### Performance Tuning

```python
# In ollama_chat.py, modify these settings:
temperature=0.7,        # Creativity (0.0-1.0)
max_tokens=1000,       # Response length
n_results=15          # Search result count
```

## 📚 Currently Available Series

### Harry Potter (Complete)

- All 7 books with plot summaries
- Main characters (Harry, Hermione, Ron)
- 📖 **Books**: Philosopher's Stone → Deathly Hallows

### Red Rising (Complete)

- All 6 books including latest trilogy
- Main characters (Darrow)
- 📖 **Books**: Red Rising → Light Bringer

## 🔍 How It Works

1. **Vector Database**: Book content is chunked and embedded in ChromaDB
2. **Semantic Search**: Your questions are matched against relevant passages
3. **Context Assembly**: Top matching passages are collected
4. **AI Generation**: Ollama generates responses based on retrieved context
5. **Filtering**: Results respect spoiler boundaries and book filters

## 🎯 Use Cases

- **Memory Refresh**: Recall plot details before reading sequels
- **Character Analysis**: Deep dive into character details
- **Spoiler-Safe**: Explore only what you've read so far

## 🚨 Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
killall ollama
ollama serve
```

### Model Not Found

```bash
# Pull the model manually
ollama pull llama3.2:latest

# List available models
ollama list
```

### ChromaDB Issues

```bash
# Reset database (WARNING: deletes all data)
rm -rf chroma_db/
python3 app/load_to_vectordb.py  # Re-index
```

### Python Dependencies

```bash
# Reinstall dependencies
pip install --upgrade -r app/requirements.txt
```

### Development

```bash
# Run in development mode
python3 app/ollama_chat.py --debug

# Test search functionality
python3 app/query.py "test query"
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
