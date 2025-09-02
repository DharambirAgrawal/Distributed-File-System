#!/bin/bash

# Cloud DFS Development Script
# This script provides common development tasks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show usage
show_usage() {
    echo "Cloud DFS Development Script"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start all services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  build       Build Docker images"
    echo "  logs        Show application logs"
    echo "  test        Run system tests"
    echo "  clean       Clean up containers and volumes"
    echo "  db-shell    Connect to database shell"
    echo "  app-shell   Connect to application shell"
    echo "  setup       Initial setup (copy .env, create directories)"
    echo "  status      Show service status"
    echo ""
}

# Setup function
setup() {
    print_status "Setting up Cloud DFS development environment..."
    
    # Copy environment file if it doesn't exist
    if [ ! -f .env ]; then
        cp .env.example .env
        print_success "Created .env file from template"
        print_warning "Please review and update .env file with your settings"
    else
        print_warning ".env file already exists"
    fi
    
    # Create directories
    mkdir -p storage uploads
    print_success "Created storage directories"
    
    print_success "Setup completed!"
    print_status "Next steps:"
    echo "  1. Review and update .env file"
    echo "  2. Run: $0 start"
    echo "  3. Visit http://localhost:5000"
}

# Start services
start() {
    print_status "Starting Cloud DFS services..."
    docker-compose up -d --build
    print_success "Services started!"
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    print_status "Service URLs:"
    echo "  Web Interface: http://localhost:5000"
    echo "  Database Admin: http://localhost:8080 (admin@dfs.local / admin)"
    echo ""
    echo "To view logs: $0 logs"
    echo "To run tests: $0 test"
}

# Stop services
stop() {
    print_status "Stopping Cloud DFS services..."
    docker-compose down
    print_success "Services stopped!"
}

# Restart services
restart() {
    print_status "Restarting Cloud DFS services..."
    docker-compose down
    docker-compose up -d --build
    print_success "Services restarted!"
}

# Build images
build() {
    print_status "Building Docker images..."
    docker-compose build
    print_success "Images built!"
}

# Show logs
logs() {
    print_status "Showing application logs..."
    docker-compose logs -f web
}

# Run tests
test() {
    print_status "Running system tests..."
    
    # Check if services are running
    if ! docker-compose ps | grep -q "Up"; then
        print_warning "Services are not running. Starting them first..."
        start
        sleep 15
    fi
    
    # Run the test script
    python3 test_system.py
}

# Clean up
clean() {
    print_warning "This will remove all containers, volumes, and local storage!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up..."
        docker-compose down -v
        docker system prune -f
        rm -rf storage/* uploads/*
        print_success "Cleanup completed!"
    else
        print_status "Cleanup cancelled"
    fi
}

# Database shell
db_shell() {
    print_status "Connecting to database..."
    docker-compose exec postgres psql -U dfs_user -d dfs_db
}

# Application shell
app_shell() {
    print_status "Connecting to application container..."
    docker-compose exec web bash
}

# Status
status() {
    print_status "Service Status:"
    docker-compose ps
    echo ""
    
    print_status "Container Health:"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}"
    echo ""
    
    if docker-compose ps | grep -q "Up"; then
        print_status "Testing web interface..."
        if curl -s http://localhost:5000 > /dev/null; then
            print_success "Web interface is accessible"
        else
            print_error "Web interface is not accessible"
        fi
    fi
}

# Main script logic
case "$1" in
    setup)
        setup
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    build)
        build
        ;;
    logs)
        logs
        ;;
    test)
        test
        ;;
    clean)
        clean
        ;;
    db-shell)
        db_shell
        ;;
    app-shell)
        app_shell
        ;;
    status)
        status
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
