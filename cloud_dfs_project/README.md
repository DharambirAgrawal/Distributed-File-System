# 🌩️ Cloud-Integrated Distributed File System MVP

A modern **Distributed File System (DFS)** with **Google Cloud Storage** integration, built with **Flask**, **PostgreSQL**, and **Docker**. This project demonstrates distributed storage, file chunking, cloud backup, fault tolerance, and RESTful API design.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen)
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Storage-orange)

## 🚀 Features

### Core Functionality
- **📦 File Chunking**: Automatic splitting of files into configurable chunks (default: 1MB)
- **💾 Local Storage**: Fast local chunk storage with PostgreSQL metadata
- **☁️ Cloud Backup**: Seamless Google Cloud Storage integration
- **🔄 Fault Tolerance**: Automatic chunk recovery from cloud when local chunks are missing
- **🔒 Data Integrity**: SHA256 checksums for file verification

### Interfaces
- **🌐 Web UI**: Clean Bootstrap-based interface for upload, download, and management
- **🔌 REST API**: Complete RESTful API for programmatic access
- **📊 Real-time Stats**: Storage usage monitoring and file statistics

### Technology Stack
- **Backend**: Python 3.11, Flask, SQLAlchemy
- **Database**: PostgreSQL 15
- **Cloud**: Google Cloud Storage
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Containerization**: Docker & Docker Compose

## 📁 Project Structure

```
cloud_dfs_project/
│
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes.py                # Web and API routes
│   ├── models.py                # Database models
│   ├── storage/
│   │   ├── chunker.py           # File chunking logic
│   │   ├── local_storage.py     # Local storage operations
│   │   └── cloud_storage.py     # Google Cloud Storage integration
│   └── templates/
│       ├── base.html            # Base template
│       ├── index.html           # Homepage
│       ├── upload.html          # Upload interface
│       └── files.html           # File management
│
├── config.py                    # Configuration management
├── app.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── docker-compose.yml           # Multi-service orchestration
├── init-db.sql                  # Database initialization
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## 🛠️ Quick Start

### Prerequisites
- **Docker** and **Docker Compose**
- **Google Cloud Account** (optional, for cloud backup)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd cloud_dfs_project

# Copy environment configuration
cp .env.example .env

# Edit .env file with your settings (optional for basic setup)
nano .env
```

### 2. Start the Application

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Access the Application

- **Web Interface**: http://localhost:5000
- **API Documentation**: Available at homepage
- **Database Admin** (optional): http://localhost:8080 (pgAdmin)

### 4. Test the System

1. Visit http://localhost:5000
2. Navigate to "Upload Files"
3. Upload a test file
4. Check "Files" page to see your uploaded file
5. Download the file to verify integrity

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://dfs_user:dfs_password@postgres:5432/dfs_db

# Storage
CHUNK_SIZE=1048576  # 1MB chunks
STORAGE_PATH=/app/storage

# Google Cloud Storage (Optional)
ENABLE_CLOUD_BACKUP=true
GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-credentials.json
GCS_BUCKET_NAME=your-bucket-name
```

### Google Cloud Storage Setup (Optional)

1. **Create a GCP Project and Storage Bucket**:
   ```bash
   # Create bucket
   gsutil mb gs://your-dfs-bucket
   ```

2. **Create Service Account**:
   ```bash
   # Create service account
   gcloud iam service-accounts create dfs-storage-account
   
   # Create and download key
   gcloud iam service-accounts keys create gcp-credentials.json \
     --iam-account=dfs-storage-account@your-project.iam.gserviceaccount.com
   ```

3. **Grant Permissions**:
   ```bash
   # Grant storage permissions
   gcloud projects add-iam-policy-binding your-project \
     --member="serviceAccount:dfs-storage-account@your-project.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   ```

4. **Update Configuration**:
   ```bash
   # Update .env file
   ENABLE_CLOUD_BACKUP=true
   GCS_BUCKET_NAME=your-dfs-bucket
   ```

## 🔌 API Documentation

### Authentication
Currently, no authentication is required (MVP setup). In production, implement proper authentication.

### Endpoints

#### Files Management

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| `GET` | `/api/files` | List all files | - |
| `POST` | `/api/files` | Upload a file | `multipart/form-data` with `file` field |
| `GET` | `/api/files/{id}` | Download a file | - |
| `POST` | `/api/files/{id}/sync` | Sync file to cloud | - |
| `DELETE` | `/api/files/{id}` | Delete a file | - |

#### System Information

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/storage/usage` | Get storage statistics |

### Example API Usage

```bash
# Upload a file
curl -X POST -F "file=@example.pdf" http://localhost:5000/api/files

# List files
curl http://localhost:5000/api/files

# Download a file
curl -o downloaded_file.pdf http://localhost:5000/api/files/1

# Sync to cloud
curl -X POST http://localhost:5000/api/files/1/sync

# Get storage usage
curl http://localhost:5000/api/storage/usage
```

## 🏗️ Architecture

### File Processing Flow

1. **Upload**: File → Chunking → Local Storage → Metadata DB → Cloud Backup
2. **Download**: Metadata DB → Chunk Assembly → File Reconstruction
3. **Fault Recovery**: Missing Chunks → Cloud Recovery → Local Restoration

### Component Interaction

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web/API UI    │    │  Flask Routes   │    │   Storage Layer │
│                 │───▶│                 │───▶│                 │
│ Upload/Download │    │ Business Logic  │    │ Chunker/Local   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │ Google Cloud    │
                       │                 │    │                 │
                       │ Metadata Store  │    │ Backup Storage  │
                       └─────────────────┘    └─────────────────┘
```

## 🔧 Development

### Running Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL
createdb dfs_db

# Set environment variables
export DATABASE_URL=postgresql://username:password@localhost/dfs_db
export STORAGE_PATH=./storage

# Run the application
python app.py
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests (when implemented)
pytest tests/
```

### Adding New Features

1. **Storage Backends**: Extend `app/storage/` with new storage providers
2. **Authentication**: Add auth middleware in `app/routes.py`
3. **File Types**: Implement type-specific handling in `app/storage/chunker.py`
4. **Monitoring**: Add metrics collection in `app/routes.py`

## 📊 Monitoring & Management

### Storage Usage

Monitor storage usage through:
- Web interface: Visit `/files` page
- API endpoint: `GET /api/storage/usage`
- Database queries: Direct PostgreSQL access

### Logs

```bash
# View application logs
docker-compose logs web

# View database logs
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f web
```

### Database Management

Access pgAdmin (optional):
1. Visit http://localhost:8080
2. Login: `admin@dfs.local` / `admin`
3. Connect to PostgreSQL server:
   - Host: `postgres`
   - Username: `dfs_user`
   - Password: `dfs_password`

## 🚀 Production Deployment

### Security Considerations

```bash
# 1. Change default passwords
# 2. Enable HTTPS
# 3. Implement authentication
# 4. Restrict database access
# 5. Use secrets management
# 6. Enable logging and monitoring
```

### Scaling Options

- **Horizontal Scaling**: Multiple Flask instances behind a load balancer
- **Database Scaling**: PostgreSQL replicas and connection pooling
- **Storage Scaling**: Multiple storage nodes with consistent hashing
- **Cloud Scaling**: Multiple cloud storage providers for redundancy

## 🐛 Troubleshooting

### Common Issues

1. **Container fails to start**:
   ```bash
   docker-compose logs web
   # Check environment variables and dependencies
   ```

2. **Database connection error**:
   ```bash
   docker-compose ps
   # Ensure postgres container is healthy
   ```

3. **File upload fails**:
   ```bash
   # Check storage directory permissions
   docker-compose exec web ls -la /app/storage
   ```

4. **Cloud sync not working**:
   ```bash
   # Verify GCP credentials and permissions
   docker-compose exec web python -c "from app.storage.cloud_storage import CloudStorage; print(CloudStorage('test-bucket').is_enabled())"
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit a pull request with detailed description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask** community for excellent web framework
- **Google Cloud** for reliable storage services
- **PostgreSQL** for robust database capabilities
- **Bootstrap** for responsive UI components

---

## 📞 Support

For questions or support:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

**Built with ❤️ for learning distributed systems and cloud integration**
