<div align="center">

# 🔬 ResearchMate — AI Research Assistant with RAG & LLMs

**An AI-powered research assistant that revolutionizes how researchers discover, analyze, and manage academic literature using advanced Retrieval-Augmented Generation (RAG) and large language models.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Tech Stack:** Python • FastAPI • Transformers • Groq (LLaMA 3.3 70B) • ChromaDB • RAG

> 📖 Built as a solo effort to deepen my understanding of modern NLP stacks — including RAG pipelines, citation graph analysis, and LLM-powered literature review generation.

</div>

---

## 🎯 Project Overview

**ResearchMate** is a full-stack research assistant system designed to explore the integration of **Retrieval-Augmented Generation (RAG)** pipelines, **citation graph analysis**, and **task-specific prompting** for academic research support. Built entirely as a solo project, it serves as a practical study in applying LLMs (specifically Groq-hosted LLaMA 3.3 70B) to literature review automation, scientific Q&A, and research trend analysis.

### 🔍 Motivation

The academic landscape is increasingly characterized by:
- **Rapid publication velocity**, making it difficult to track developments in a domain
- **Shallow context understanding** in traditional keyword-based retrieval tools (e.g., Google Scholar, Semantic Scholar)
- **Disjointed workflows**, where search, summarization, and citation management are siloed

This project aims to build an integrated system where these capabilities are unified using **RAG + vector search + LLM-based synthesis**, offering a more coherent and semantically rich research workflow.

### ⚙️ Technical Goals

- Implement a **custom RAG pipeline** for semantic search and summarization over paper corpora
- Develop **project-based research management**, enabling storage and recall of paper sets by topic
- Use **ChromaDB** for document vector storage, embedding papers with Sentence Transformers
- Perform **citation network analysis**, extracting structured citation graphs from uploaded PDFs
- Run LLM inference using **Groq Cloud (LLaMA 3.3 70B)** for high-throughput, low-latency generation
- Support **multi-turn question-answering**, trend detection, and review generation over paper clusters
- Enable **upload and PDF parsing**, converting documents into extractive + abstractive summaries

### 🔬 Learning Focus

This project was built for the purpose of:
- Deepening my understanding of **LLM application architectures**, especially RAG
- Experimenting with **embedding-based search**, hybrid pipelines, and LLM prompting
- Building robust backends using **FastAPI**, integrating with frontend templates and API routes
- Handling real-world constraints like **low-resource deployment**, **cold-start initialization**, and **secure multi-user access**

---

## 🧠 Core Technologies & Architecture

### Retrieval-Augmented Generation (RAG) System

ResearchMate implements a sophisticated RAG pipeline that combines retrieval mechanisms with generative AI:

```
Query → Embedding → Vector Search → Context Retrieval → LLM Generation → Response
```

**Key Components:**

1. **Document Processing Pipeline**
   - PDF text extraction with advanced cleaning
   - Chunking strategies for optimal retrieval
   - Metadata extraction (authors, titles, citations)

2. **Vector Database (ChromaDB)**
   - Semantic embeddings for research papers
   - Efficient similarity search
   - Persistent storage for knowledge bases

3. **Language Model Integration (Groq Llama 3.3 70B)**
   - High-performance inference
   - Context-aware response generation
   - Multi-turn conversation support

4. **Retrieval Engine**
   - Semantic search capabilities
   - Contextual ranking algorithms
   - Multi-modal retrieval (text, metadata, citations)

### Technical Stack

#### AI & Machine Learning
- **LLM**: Groq Llama 3.3 70B (ultra-fast inference)
- **Embeddings**: Sentence Transformers for semantic search
- **Vector Database**: ChromaDB for efficient similarity search
- **RAG Framework**: Custom implementation with advanced retrieval strategies

#### Backend
- **Framework**: FastAPI (high-performance async Python web framework)
- **Authentication**: JWT-based secure user management
- **PDF Processing**: PyMuPDF, pdfplumber, pypdf for robust text extraction
- **Data Storage**: JSON files for user data, ChromaDB for vector storage

#### Frontend
- **Framework**: Vanilla JavaScript with modern ES6+ features
- **UI Library**: Bootstrap 5 for responsive design
- **Visualization**: Chart.js for research analytics and trends
- **Icons**: Font Awesome for consistent iconography

#### Development & Infrastructure
- **Development Server**: Custom server with hot-reload capabilities
- **Containerization**: Docker and Docker Compose
- **Deployment**: Render-ready with environment-based configuration
- **Monitoring**: Health checks and comprehensive logging

## ✨ Features & Capabilities

### 🔍 Intelligent Paper Search
- **Natural Language Queries**: Search using conversational language
- **Semantic Understanding**: Goes beyond keyword matching
- **Multi-source Integration**: Searches across multiple academic databases
- **Real-time Results**: Fast, responsive search experience

### 🧠 AI-Powered Analysis
- **Document Summarization**: Generate concise summaries of research papers
- **Key Insight Extraction**: Identify main contributions and findings
- **Comparative Analysis**: Compare multiple papers and methodologies
- **Question Answering**: Get specific answers from research content

### 📚 Project Management
- **Research Projects**: Organize papers into themed collections
- **Literature Reviews**: Automatically generate comprehensive reviews
- **Knowledge Graphs**: Visualize connections between research areas
- **Progress Tracking**: Monitor research milestones and discoveries

### 📊 Citation Network Analysis
- **Reference Mapping**: Visualize citation relationships
- **Impact Analysis**: Assess paper influence and importance
- **Research Lineage**: Track the evolution of research ideas
- **Collaboration Networks**: Identify key researchers and institutions

### 📈 Research Trend Monitoring
- **Trend Detection**: Identify emerging research areas
- **Temporal Analysis**: Track research evolution over time
- **Predictive Insights**: Forecast future research directions
- **Comparative Studies**: Analyze trends across different fields

### 📄 Advanced PDF Processing
- **Text Extraction**: High-quality text extraction from academic PDFs
- **Structure Recognition**: Identify sections, abstracts, references
- **Metadata Extraction**: Extract author information, publication details
- **Content Cleaning**: Remove formatting artifacts and noise

---

## 🔧 RAG System Deep Dive

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   Query Engine  │───▶│   Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Generated     │◀───│   LLM Engine    │◀───│  Vector Search  │
│   Response      │    │  (Groq Llama)   │    │   (ChromaDB)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Context       │◀───│   Document      │
                       │   Builder       │    │   Retriever     │
                       └─────────────────┘    └─────────────────┘
```

### Key Components

#### 1. Document Processing (`pdf_processor.py`)
- **Multi-library PDF extraction** for robust text extraction
- **Content cleaning** to remove formatting artifacts
- **Intelligent chunking** with overlap for context preservation
- **Metadata extraction** for enhanced search capabilities

#### 2. Vector Storage (`rag_system.py`)
- **ChromaDB integration** for efficient vector operations
- **Semantic embeddings** using Sentence Transformers
- **Persistent storage** for knowledge base persistence
- **Similarity search** with configurable parameters

#### 3. Query Processing (`groq_processor.py`)
- **Query understanding** and intent recognition
- **Context retrieval** from vector database
- **Prompt engineering** for optimal LLM performance
- **Response generation** with citation tracking

#### 4. Research Assistant (`research_assistant.py`)
- **Multi-turn conversations** with context awareness
- **Project-based knowledge** management
- **Literature review** generation
- **Trend analysis** and insights

### RAG Implementation Details

#### Chunking Strategy
```python
# Configurable chunking parameters
CHUNK_SIZE = 1000        # Characters per chunk
CHUNK_OVERLAP = 200      # Overlap between chunks
```

#### Retrieval Process
1. **Query Embedding**: Convert user query to vector representation
2. **Similarity Search**: Find most relevant document chunks
3. **Context Assembly**: Combine retrieved chunks with metadata
4. **Response Generation**: Generate answer using retrieved context

#### Context Management
- **Conversation history** for multi-turn interactions
- **Project context** for domain-specific responses
- **Citation tracking** for source attribution
- **Relevance scoring** for answer quality

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Groq API key ([Get one here](https://console.groq.com/))
- 4GB+ RAM recommended for optimal performance

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ananthakr1shnan/ResearchMate.git
cd ResearchMate
```

2. **Set up virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

5. **Run the application**
```bash
# Development server (recommended)
python src/scripts/dev_server.py

# Or basic server
python main.py
```

6. **Access the application**
- Web Interface: http://127.0.0.1:8000
- API Documentation: http://127.0.0.1:8000/docs
- Interactive API: http://127.0.0.1:8000/redoc


---

## 🛠️ Development Workflow

### Development Server
The development server provides a rich development experience:

```bash
# Start development server
python src/scripts/dev_server.py

# Custom configuration
python src/scripts/dev_server.py --host 0.0.0.0 --port 8080 --no-browser

# Run with code quality checks
python src/scripts/dev_server.py --lint

# Run tests
python src/scripts/dev_server.py --test
```

**Development server features:**
- ✅ Automatic port management
- ✅ File change detection
- ✅ Browser auto-launch
- ✅ Development-friendly logging
- ✅ Same codebase as production

### Management System
Use the comprehensive management system:

```bash
# System status
python src/scripts/manager.py status

# Dependency management
python src/scripts/manager.py install

# Server management
python src/scripts/manager.py dev      # Development
python src/scripts/manager.py start    # Production

# Data management
python src/scripts/manager.py backup
python src/scripts/manager.py restore --backup-name backup_20250713_120000
python src/scripts/manager.py list-backups

# Maintenance
python src/scripts/manager.py clean-logs
python src/scripts/manager.py reset-db
```

---

## 📖 Usage Examples

### Web Interface

1. **Create a Research Project**
   - Navigate to Projects tab
   - Click "New Project"
   - Upload relevant papers or search for literature

2. **Search and Analyze**
   - Use natural language queries: "What are the latest advances in transformer architectures?"
   - Get AI-generated summaries with citations
   - Explore related papers and concepts

3. **Generate Literature Reviews**
   - Select papers from your project
   - Click "Generate Review"
   - Get comprehensive analysis with key insights

### API Integration

```python
import requests

# Authentication
response = requests.post("http://127.0.0.1:8000/api/login", json={
    "username": "researcher",
    "password": "secure_password"
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Semantic search
response = requests.post("http://127.0.0.1:8000/api/search", 
    json={"query": "neural networks for natural language processing"}, 
    headers=headers
)
results = response.json()

# Ask questions about retrieved papers
response = requests.post("http://127.0.0.1:8000/api/ask",
    json={"question": "What are the computational advantages of attention mechanisms?"},
    headers=headers
)
answer = response.json()

# Upload and analyze papers
files = {"file": open("research_paper.pdf", "rb")}
response = requests.post("http://127.0.0.1:8000/api/upload", 
    files=files, headers=headers
)
analysis = response.json()
```

## 🚀 Deployment

### Docker Deployment (Recommended)

```bash
# Build and run
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Traditional Server Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=your_key_here

# Run production server
python main.py
```


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

