# 🌩️ Distributed File System

This repository contains a **Local Distributed File System with User Authentication** built with Flask, PostgreSQL, and local backup storage.

## 🚀 Quick Start

```bash
cd cloud_dfs_project
./dev.sh setup
./dev.sh start
```

Then visit: **http://localhost:5000**

## 📁 Project Location

The complete project is located in the `cloud_dfs_project/` directory.

👉 **[Go to Project →](./cloud_dfs_project/)**

## ✨ Features

- **User Authentication**: Secure registration, login, and user isolation
- **File Chunking & Distribution**: Automatic file splitting for distributed storage
- **Local Backup**: Local filesystem backup with fault tolerance
- **User Isolation**: Each user has secure, separate file storage
- **Web Interface**: Clean Bootstrap UI with user management
- **REST API**: Complete RESTful API with authentication
- **Docker Ready**: Full containerization with Docker Compose
- **Real-time Monitoring**: Storage usage and file statistics

Built with Python, Flask, PostgreSQL, Flask-Login, and local storage.