# AI Research Assistant - MVP

A Flask-based web application for personal research file management with user authentication, file upload capabilities, and a tagging system.

## Features

### ✅ Implemented (MVP Version)

- **User Authentication**

  - User signup and login with username/password
  - Password hashing using bcrypt
  - Session management
  - Secure user authentication

- **File Upload & Management**

  - Upload files (TXT, PDF, DOC, DOCX, PNG, JPG, JPEG, GIF)
  - View uploaded files with metadata
  - Delete files
  - Per-user file storage directories

- **Tagging System**

  - Add tags to uploaded files
  - Remove tags from files
  - View files with their associated tags

- **Web Interface**
  - Clean, responsive web UI
  - Login/Signup pages
  - Dashboard for file management
  - File upload interface

## Project Structure

```
ai_research_assistant/
│
├── main.py                # Flask app entry point
├── requirements.txt       # Python dependencies
├── uploads/               # User file storage (created automatically)
│
├── templates/             # HTML templates
│   ├── base.html         # Base template with shared styling
│   ├── login.html        # Login page
│   ├── signup.html       # User registration
│   ├── dashboard.html    # Main dashboard
│   └── upload.html       # File upload interface
│
├── user/
│   └── auth.py           # User authentication logic
│
├── storage/
│   └── uploader.py       # File upload/management logic
│
├── db/
│   ├── database.py       # Database connection and utilities
│   └── models.sql        # PostgreSQL schema
│
├── utils/
│   └── file_utils.py     # File system utilities
│
└── README.md
```

## Database Schema

### Users Table

```sql
users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Documents Table

```sql
documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    summary TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Tags Table

```sql
tags (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Installation & Setup

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- PostgreSQL database (optional – the app now defaults to a bundled SQLite database for local development)

### Environment Setup

1. **Clone/Navigate to the project directory**

   ```bash
   cd /workspaces/Distributed-File-System/ai_research_assistant
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**

   Create a `.env` file (or export variables in your shell) if you want to customise the configuration:

   ```env
   # Optional: only needed when using PostgreSQL
   DATABASE_URL=postgresql://username:password@host:5432/database_name

   # Optional: override the default SQLite file location
   SQLITE_DB_PATH=/absolute/path/to/ai_research.db

   # Flask session secret
   SECRET_KEY=change-me-in-production
   ```

   If `DATABASE_URL` is not provided, the application automatically uses the SQLite database located at `db/ai_research.db`.

4. **Run the application**

   ```bash
   python main.py
   ```

5. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Create a new account or login

## Usage

### Getting Started

1. **Sign Up**: Create a new account with a username and password
2. **Login**: Access your personal dashboard
3. **Upload Files**: Use the upload interface to add files
4. **Manage Files**: View, tag, and delete your files from the dashboard
5. **Organize**: Add meaningful tags to categorize your files

### File Management

- **Supported Formats**: TXT, PDF, DOC, DOCX, PNG, JPG, JPEG, GIF
- **File Storage**: Files are stored in user-specific directories
- **File Operations**: Upload, view metadata, delete
- **Tagging**: Add/remove tags for better organization

### Security Features

- Password hashing with bcrypt
- User session management
- File access control (users can only access their own files)
- Secure file upload with filename sanitization

## API Endpoints

- `GET /` - Home page (redirects based on login status)
- `GET/POST /login` - User login
- `GET/POST /signup` - User registration
- `GET /logout` - User logout
- `GET /dashboard` - User dashboard
- `GET/POST /upload` - File upload
- `GET /delete_file/<id>` - Delete file
- `POST /add_tag/<id>` - Add tag to file
- `GET /remove_tag/<id>/<tag>` - Remove tag from file

## Future Enhancements (Not in MVP)

- AI-powered document analysis
- Advanced search functionality
- File sharing between users
- Document summarization
- OCR for image files
- Advanced tagging with auto-suggestions
- File version control
- Export/import functionality

## Contributing

This is an MVP version. Future enhancements will include:

- AI integration for document analysis
- Advanced search and filtering
- Real-time collaboration features
- API endpoints for external integrations

## License

This project is for educational/demonstration purposes.

---

**Note**: This is the MVP (Minimum Viable Product) version focusing on core functionality. Advanced features like AI integration, search algorithms, and distributed file systems will be added in future iterations.
