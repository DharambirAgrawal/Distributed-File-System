# 🔍 AI-Powered Personal Research Assistant - Enhanced with Search

A Flask-based web application for personal research file management with **intelligent search capabilities**, user authentication, file upload, and advanced tagging system.

## 🎯 Latest Update: Intelligent Search System

The application now includes a comprehensive search engine with multiple algorithms:

### 🔍 **Search Features**

- **🔄 Multiple Search Algorithms**

  - **BFS (Breadth-First Search)**: Level-by-level search (filenames → tags → summaries → content)
  - **⬇️ DFS (Depth-First Search)**: Deep document-by-document search
  - **⭐ A\* Search**: Smart heuristic-based search with relevance scoring

- **📄 Full-Text Content Indexing**

  - Automatic text extraction from uploaded files
  - Searchable content from TXT, PDF, DOCX files
  - OCR support for images (PNG, JPG, JPEG, GIF)

- **🎯 Multi-Field Search**

  - Search across file names, tags, summaries, and document content
  - Context-aware result snippets
  - Relevance scoring and ranking

- **📊 Search Analytics**
  - Search query logging with algorithm performance metrics
  - Execution time tracking
  - Results count analytics

## ✅ **Complete Feature Set**

### 🔐 **User Authentication**

- Secure signup/login with bcrypt password hashing
- Session management and user isolation
- Per-user data access controls

### 📁 **File Management & Text Extraction**

- Upload files: TXT, PDF, DOC, DOCX, PNG, JPG, JPEG, GIF
- **NEW**: Automatic text extraction and indexing
- **NEW**: Full-text content storage for searching
- File metadata management
- Secure per-user storage directories

### 🏷️ **Advanced Tagging System**

- Manual tag assignment and removal
- Tag-based search and filtering
- Multi-tag support per document

### 🌐 **Enhanced Web Interface**

- **NEW**: Advanced search interface with algorithm selection
- **NEW**: Document viewer with full-text content display
- **NEW**: Search results with context snippets
- Responsive design with clean UI
- Flash messaging system

### 🗄️ **Enhanced Database Schema**

- **NEW**: `full_text_content` column for searchable content
- **NEW**: `search_logs` table for analytics
- **NEW**: Full-text search indexes (PostgreSQL GIN)
- Foreign key relationships and data integrity

## 🏗️ **Project Structure**

```
ai_research_assistant/
│
├── main.py                    # Flask app with search routes
├── requirements.txt           # Updated dependencies
├── setup.sh                  # Setup script
├── test_app.py               # Application testing
├── uploads/                  # User file storage
│
├── templates/                # HTML templates
│   ├── base.html            # Base template with search nav
│   ├── login.html           # Login page
│   ├── signup.html          # User registration
│   ├── dashboard.html       # Main dashboard
│   ├── upload.html          # File upload
│   ├── search.html          # NEW: Search interface
│   └── view_document.html   # NEW: Document viewer
│
├── user/
│   └── auth.py              # User authentication
│
├── storage/
│   └── uploader.py          # File upload with text extraction
│
├── search/                  # NEW: Search engine
│   ├── __init__.py
│   └── algorithms.py        # BFS, DFS, A* implementations
│
├── db/
│   ├── database.py          # Database utilities (PostgreSQL or SQLite)
│   ├── models.sql           # Enhanced PostgreSQL schema
│   └── models_sqlite.sql    # SQLite schema for local development
│
├── utils/
│   └── file_utils.py        # File utilities + text extraction
│
├── README.md                # This file
└── DEPLOYMENT.md            # Deployment guide
```

## 🗄️ **Enhanced Database Schema**

### Documents Table (Updated)

```sql
documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    file_name VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    summary TEXT NULL,
    full_text_content TEXT NULL,        -- NEW: Searchable content
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Search Logs Table (New)

```sql
search_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    query VARCHAR(500) NOT NULL,
    algorithm_used VARCHAR(50) NOT NULL,
    results_count INTEGER DEFAULT 0,
    execution_time_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## 🔍 **Search Algorithm Details**

### 1. BFS (Breadth-First Search)

- **Strategy**: Searches all documents at each level before going deeper
- **Order**: File names → Tags → Summaries → Full content
- **Best For**: Finding exact matches in metadata first
- **Use Case**: When you know the filename or have specific tags

### 2. DFS (Depth-First Search)

- **Strategy**: Searches deeply within each document before moving to next
- **Order**: Per document: filename → tags → summary → content
- **Best For**: Comprehensive search within individual documents
- **Use Case**: When you want thorough analysis of each document

### 3. A\* Search

- **Strategy**: Uses intelligent heuristics to prioritize most relevant documents
- **Heuristic**: Word overlap, content relevance, document length penalty
- **Best For**: Finding most relevant results efficiently
- **Use Case**: General search when you want the best results first

## 🚀 **Getting Started**

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- PostgreSQL database (optional – the app defaults to a bundled SQLite database when `DATABASE_URL` is not provided)

### Installation

1. **Install dependencies**

   ```bash
   cd ai_research_assistant
   pip install -r requirements.txt
   ```

2. **Environment Setup**

Create a `.env` file (or export variables in your shell) if you need to override the defaults:

```env
# Optional: PostgreSQL connection string
DATABASE_URL=postgresql://username:password@host:5432/database_name

# Optional: custom path for the SQLite database file
SQLITE_DB_PATH=/absolute/path/to/ai_research.db

# Flask session secret
SECRET_KEY=change-me-in-production
```

> ℹ️ When no `DATABASE_URL` is supplied the application automatically uses `db/ai_research.db` (SQLite), making local setup zero-config.

3. **Start the application**

   ```bash
   python main.py
   ```

4. **Access the application**
   - Open `http://localhost:5000`
   - Create an account and start uploading files
   - Use the search feature to find your documents

## 🔍 **Using the Search Feature**

1. **Upload Documents**: Files are automatically indexed for text content
2. **Choose Algorithm**: Select BFS, DFS, or A\* based on your search needs
3. **Enter Query**: Search for keywords, phrases, or specific terms
4. **View Results**: Results show relevance scores and context snippets
5. **Browse Documents**: Click to view full document content

### Search Tips

- **BFS**: Best for finding files by name or tags
- **DFS**: Best for deep content analysis
- **A\***: Best for general searches with smart ranking
- Use specific keywords for better results
- Search supports partial word matching

## 📊 **Performance & Analytics**

- **Search Logging**: All searches are logged with performance metrics
- **Execution Time**: Search times are measured and displayed
- **Result Ranking**: Results are scored and ranked by relevance
- **Context Snippets**: Matching text is highlighted in results

## 🔧 **API Endpoints**

### New Search Endpoints

- `GET/POST /search` - Main search interface
- `GET /view_document/<id>` - Document viewer

### Existing Endpoints

- `GET /` - Home page (redirects)
- `GET/POST /login` - User authentication
- `GET/POST /signup` - User registration
- `GET /dashboard` - User dashboard
- `GET/POST /upload` - File upload
- `GET /delete_file/<id>` - Delete file
- `POST /add_tag/<id>` - Add tag
- `GET /remove_tag/<id>/<tag>` - Remove tag

## 🔮 **Future Enhancements**

The current implementation provides the perfect foundation for:

- **🤖 AI Integration**: Gemini API for semantic search
- **📊 Advanced Analytics**: Search pattern analysis
- **🔄 Real-time Search**: Live search suggestions
- **📱 Mobile App**: React Native or Flutter client
- **🔗 API Integration**: RESTful API for external tools
- **📈 Machine Learning**: Search result optimization

## 📝 **Technical Implementation**

### Text Extraction Pipeline

1. **File Upload** → **Text Extraction** → **Database Storage**
2. **Supported Formats**: TXT (direct), PDF (PyPDF2), DOCX (python-docx), Images (OCR)
3. **Search Indexing**: PostgreSQL GIN indexes for fast full-text search

### Search Algorithm Implementation

- **Object-Oriented Design**: SearchResult classes and DocumentSearcher
- **Database Integration**: Efficient queries with proper indexing
- **Performance Optimization**: Relevance scoring and result limiting
- **Error Handling**: Comprehensive exception management

---

**🎉 Your AI Research Assistant now has intelligent search capabilities!**

The application successfully combines traditional file management with modern search algorithms, providing a solid foundation for future AI enhancements.
