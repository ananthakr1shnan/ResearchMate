# ResearchMate 🔬

An AI-powered research assistant that helps you search, analyze, and manage academic papers using advanced language models.

## Features ✨

- **🔍 Smart Paper Search**: Search academic papers using natural language queries
- **🧠 AI-Powered Analysis**: Analyze papers and generate insights using Groq Llama 3.3 70B
- **📚 Project Management**: Organize research into projects with automatic literature management
- **📊 Citation Network Analysis**: Visualize and analyze citation networks
- **📈 Research Trend Monitoring**: Track and monitor research trends over time
- **📄 PDF Processing**: Extract and process text from PDF papers with advanced cleaning
- **🔐 User Authentication**: Secure user management with JWT tokens
- **💾 Vector Storage**: Efficient paper storage and retrieval using ChromaDB

## Quick Start 🚀

### Prerequisites
- Python 3.8+
- Groq API key (for LLM functionality)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/ananthakr1shnan/ResearchMate.git
cd ResearchMate
```

2. **Create virtual environment**:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

5. **Run the application**:
```bash
python main.py
```

6. **Access the application**:
- Web Interface: http://127.0.0.1:8000
- API Documentation: http://127.0.0.1:8000/docs

## Development Setup �️

### Development Server

ResearchMate includes a comprehensive development server with auto-reload, file watching, and smart port management:

```bash
# Start development server (recommended for development)
python src/scripts/dev_server.py

# Start with custom host/port
python src/scripts/dev_server.py --host 0.0.0.0 --port 8080

# Start without opening browser automatically
python src/scripts/dev_server.py --no-browser

# Run code quality checks
python src/scripts/dev_server.py --lint

# Run tests
python src/scripts/dev_server.py --test
```

**Development server features:**
- ✅ Smart port management (automatically finds available ports)
- ✅ File watching for automatic reload notifications
- ✅ Browser auto-open
- ✅ Same codebase as production
- ✅ Development-friendly logging

### Management Scripts

Use the management system for various operations:

```bash
# Show system status
python src/scripts/manager.py status

# Install/update dependencies
python src/scripts/manager.py install

# Start development server via manager
python src/scripts/manager.py dev

# Start production server
python src/scripts/manager.py start

# Run tests
python src/scripts/manager.py test

# Backup data
python src/scripts/manager.py backup

# Restore from backup
python src/scripts/manager.py restore --backup-name backup_20250713_120000

# List available backups
python src/scripts/manager.py list-backups

# Clean old logs
python src/scripts/manager.py clean-logs

# Reset database
python src/scripts/manager.py reset-db
```

### Project Structure

```
ResearchMate/
├── main.py                    # Main application entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
├── .gitignore                 # Git ignore rules
├── .dockerignore             # Docker ignore rules
├── DEPLOYMENT.md             # Deployment instructions
├── src/
│   ├── components/           # Core application components
│   │   ├── auth.py          # Authentication system
│   │   ├── groq_processor.py # Groq AI integration
│   │   ├── pdf_processor.py  # PDF processing utilities
│   │   ├── rag_system.py     # RAG (Retrieval-Augmented Generation)
│   │   └── research_assistant.py # Main research logic
│   ├── scripts/             # Development and management scripts
│   │   ├── dev_server.py    # Development server
│   │   ├── manager.py       # Management system
│   │   └── deploy.py        # Deployment scripts
│   ├── static/              # Frontend assets
│   │   ├── css/main.css     # Styles
│   │   └── js/main.js       # JavaScript
│   └── templates/           # HTML templates
│       ├── base.html        # Base template
│       ├── index.html       # Home page
│       ├── login.html       # Login page
│       ├── projects.html    # Projects page
│       ├── search.html      # Search interface
│       ├── trends.html      # Trends analysis
│       └── upload.html      # File upload
├── data/                    # Data storage (auto-created)
├── logs/                    # Application logs (auto-created)
├── chroma_persist/          # ChromaDB storage (auto-created)
└── backups/                 # Data backups (auto-created)
```

### Development Workflow

1. **Setup Development Environment**:
```bash
# Clone and setup
git clone https://github.com/ananthakr1shnan/ResearchMate.git
cd ResearchMate
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Start Development**:
```bash
# Start development server
python src/scripts/dev_server.py
# Server starts on http://127.0.0.1:8000 (or next available port)
```

3. **Make Changes**:
- Edit files in `src/` directory
- File changes are automatically detected
- Manual restart required for full reload

4. **Test Changes**:
```bash
# Run tests
python src/scripts/manager.py test
# or
python src/scripts/dev_server.py --test
```

5. **Code Quality**:
```bash
# Check code quality
python src/scripts/dev_server.py --lint
```

### Environment Variables

Development and production use these environment variables:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional - Development
CHUNK_SIZE=1000                    # Text chunk size for processing
CHUNK_OVERLAP=200                  # Text chunk overlap
RESEARCHMATE_HOST=127.0.0.1       # Development host
RESEARCHMATE_PORT=8000             # Development port

# Optional - Production
PORT=8000                          # Production port (used by Render)
```

### Docker Development

For containerized development:

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### API Development

The FastAPI application provides comprehensive API documentation:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

### Key API Endpoints

```bash
# Authentication
POST /api/register          # User registration
POST /api/login            # User login

# Research Operations
POST /api/search           # Search for papers
POST /api/ask             # Ask questions about papers
POST /api/upload          # Upload PDF files
POST /api/analyze         # Analyze uploaded content

# Project Management
GET  /api/projects        # Get user projects
POST /api/projects        # Create new project
GET  /api/projects/{id}   # Get specific project
POST /api/projects/{id}/question  # Ask project question

# Trends and Analytics
POST /api/trends          # Analyze research trends
GET  /api/health          # Health check endpoint
```

## Usage 📖

### Web Interface
1. **Register/Login**: Create an account or log in
2. **Create Project**: Start a new research project
3. **Search Papers**: Use natural language to search for relevant papers
4. **Upload PDFs**: Upload and analyze your own papers
5. **Ask Questions**: Get AI-powered insights and analysis
6. **Generate Reviews**: Create literature reviews automatically

### API Usage Examples

```python
import requests

# Login
response = requests.post("http://127.0.0.1:8000/api/login", json={
    "username": "your_username",
    "password": "your_password"
})
token = response.json()["access_token"]

# Search papers
headers = {"Authorization": f"Bearer {token}"}
response = requests.post("http://127.0.0.1:8000/api/search", 
    json={"query": "machine learning transformers"}, 
    headers=headers
)
results = response.json()

# Ask questions
response = requests.post("http://127.0.0.1:8000/api/ask",
    json={"question": "What are the main benefits of transformer architectures?"},
    headers=headers
)
answer = response.json()
```

## Deployment 🚀

### Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

**Quick deployment options:**

1. **Render (Recommended)**:
   - Connect GitHub repository
   - Set environment variables
   - Deploy automatically

2. **Docker**:
```bash
# Build image
docker build -t researchmate .

# Run container
docker run -p 8000:8000 -e GROQ_API_KEY=your_key researchmate
```

3. **Traditional Server**:
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=your_key

# Run application
python main.py
```

## Technology Stack 🛠️

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.8+
- **AI/ML**: Groq Llama 3.3 70B, Sentence Transformers
- **Database**: ChromaDB (vector storage), JSON (user data)
- **Authentication**: JWT tokens
- **PDF Processing**: PyMuPDF, pdfplumber, pypdf

### Frontend
- **Framework**: Vanilla JavaScript
- **UI**: Bootstrap 5, Custom CSS
- **Icons**: Font Awesome
- **Charts**: Chart.js (for analytics)

### Development Tools
- **Server**: Custom development server with file watching
- **Management**: Comprehensive management scripts
- **Containerization**: Docker & Docker Compose
- **Code Quality**: Flake8 (optional)
- **Testing**: Custom test framework

### Infrastructure
- **Hosting**: Render, Docker, or traditional servers
- **Storage**: Local filesystem, ChromaDB persistence
- **Logging**: Python logging with file rotation
- **Monitoring**: Health check endpoints

## Contributing 🤝

### Getting Started

1. **Fork the repository**
2. **Clone your fork**:
```bash
git clone https://github.com/yourusername/ResearchMate.git
cd ResearchMate
```

3. **Set up development environment**:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

4. **Start development server**:
```bash
python src/scripts/dev_server.py
```

5. **Make changes and test**:
```bash
# Test your changes
python src/scripts/manager.py test

# Check code quality
python src/scripts/dev_server.py --lint
```

6. **Submit pull request**:
```bash
git checkout -b feature/amazing-feature
git commit -m 'Add amazing feature'
git push origin feature/amazing-feature
```

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation for API changes
- Use meaningful commit messages
- Test with different Python versions if possible

### Project Management

- Issues: Report bugs and request features
- Discussions: Ask questions and share ideas
- Wiki: Additional documentation and guides
- Releases: Follow semantic versioning

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support 💬

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and community support
- **Documentation**: Check the wiki for additional guides

## Roadmap 🗺️

### Current Focus
- Enhanced PDF processing
- Improved citation network analysis
- Better search relevance
- Performance optimizations

### Future Plans
- Multi-language support
- Advanced visualization tools
- Integration with more databases
- Mobile-responsive design improvements
- Plugin system for extensions

---

**ResearchMate** - Making research smarter, one paper at a time! 🎓

*Built with ❤️ by the research community*
