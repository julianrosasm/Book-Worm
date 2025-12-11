# BookWorm 📚

A Retrieval-Augmented Generation (RAG) system that lets you chat with your favorite book series using AI. Ask questions about characters, events, and plot points from your favorite series.

## Features

- **AI-Powered Chat**: Interactive conversations about your favorite series using local Ollama models
- **Multi-purpose**: Ask about characters, events, and locations
- **Multi-Series Support**: Harry Potter, Red Rising, and easy expansion to new series
- **Multi-Category Support**: Characters, events, locations, and easy expansion to new categories (e.g. Technology)
- **Series Filtering**: Focus conversations on a specific series
- **Spoiler Prevention**: AI is instructed to avoid revealing major spoilers (e.g., character deaths) in its answers
- **Vector Search**: Semantic search through Fandom character and event information
- **Local & Private**: All processing happens locally

## Architecture
<img width="828" height="520" alt="Screenshot 2025-11-23 at 12 25 54 PM" src="https://github.com/user-attachments/assets/fd28cd01-bafd-4972-b447-9d7f646fd2d6" />

## Demo
https://github.com/user-attachments/assets/d087d110-f914-4c2b-a618-dbbcd5291e75

## Quick Start

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

# Launch BookWorm Chat (CLI)
python3 app/ollama_chat.py

# Or launch the Streamlit web app (recommended)
PYTHONPATH=$PWD streamlit run app/app_streamlit.py
```

## How to Use

### Basic Chat

```
You: Tell me about Darrow's character development
AI: Darrow undergoes significant transformation throughout the Red Rising series...
```

### Series Filtering

```
You: /series RedRising
You: Tell me about Mustang
AI: [Only uses Red Rising series information]
```

### Available Commands

- `/series <series_name>` - Filter to specific series
- `/context` - Show retrieved passages (CLI only)
- `/clear` - Reset all filters (CLI only)
- `/quit` - Exit chat

## Project Structure

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
│       │   ├── characters/  # Character information
│       │   └── events/      # Event information
│       └── RedRising/
│           ├── characters/
│           └── events/
└── chroma_db/               # Vector database
    └── chroma.sqlite3       # Persistent storage
```

## Installation Details

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

## Configuration

### Ollama Settings

Default model: `llama3.2:latest` (4.1GB)

To use a different model:

```python
# In ollama_chat.py
BookWormOllamaRAG(model_name="llama3.2:latest")
```

### Model

- `llama3.2:latest` (recommended, 4GB)

### Performance Tuning

```python
# In ollama_chat.py, modify these settings:
temperature=0.2,        # Creativity (0.0-1.0)
max_tokens=1000,       # Response length
n_results=12          # Search result count
```

## Currently Available Series

### Harry Potter (Complete)

- Main characters (Harry, Hermione, Ron)
- Key events from the series

### Red Rising (Complete)

- Main characters (Darrow and Mustang)
- Key events from the series

## How It Works

1. **Vector Database**: Book content is chunked and embedded in ChromaDB
2. **Semantic Search**: Your questions are matched against relevant passages
3. **Context Assembly**: Top matching passages are collected
4. **AI Generation**: Ollama generates responses based on retrieved context
5. **Filtering**: Results respect series filters

## Use Cases

- **Memory Refresh**: Recall plot details before reading sequels
- **Character Analysis**: Deep dive into character and event details

## Troubleshooting

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

# Run the Streamlit web app
PYTHONPATH=$PWD streamlit run app/app_streamlit.py
```
