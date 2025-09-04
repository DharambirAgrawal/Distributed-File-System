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
    echo "  start       Start all services (development mode)"
    echo "  start-prod  Start all services (production mode)"
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
    echo "  test-gunicorn  Test gunicorn deployment locally"
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
    print_status "Starting Cloud DFS services (development mode)..."
    docker-compose -f docker-compose.dev.yml up -d --build
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

# Start production-like services
start_prod() {
    print_status "Starting Cloud DFS services (production mode)..."
    docker-compose up -d --build
    print_success "Services started!"
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    print_status "Service URLs:"
    echo "  Web Interface: http://localhost:5000"
    echo ""
    echo "To view logs: $0 logs"
    echo "To run tests: $0 test"
}

# Stop services
stop() {
    print_status "Stopping Cloud DFS services..."
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    docker-compose down 2>/dev/null || true
    print_success "Services stopped!"
}

# Restart services
restart() {
    print_status "Restarting Cloud DFS services..."
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml up -d --build
    print_success "Services restarted!"
}

# Build images
build() {
    print_status "Building Docker images..."
    docker-compose -f docker-compose.dev.yml build
    print_success "Images built!"
}

# Show logs
logs() {
    print_status "Showing application logs..."
    docker-compose -f docker-compose.dev.yml logs -f web
}

# Test gunicorn deployment
test_gunicorn() {
    print_status "Testing gunicorn deployment locally..."
    
    # Build the image first
    docker build -t dfs-test .
    
    # Run with same configuration as production
    print_status "Starting container with gunicorn..."
    docker run -d --name dfs-test-container \
        -p 5001:5000 \
        -e PORT=5000 \
        -e FLASK_ENV=production \
        -e SECRET_KEY=test-secret-key \
        -e ENABLE_CLOUD_BACKUP=false \
        dfs-test
    
    # Wait and test
    sleep 10
    
    print_status "Testing health endpoint..."
    if curl -f http://localhost:5001/health > /dev/null 2>&1; then
        print_success "Gunicorn deployment test PASSED!"
        print_status "Application is running at: http://localhost:5001"
    else
        print_error "Gunicorn deployment test FAILED!"
        print_status "Checking container logs:"
        docker logs dfs-test-container
    fi
    
    print_status "To stop test container: docker stop dfs-test-container && docker rm dfs-test-container"
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
    docker-compose -f docker-compose.dev.yml exec postgres psql -U dfs_user -d dfs_db
}

# Application shell
app_shell() {
    print_status "Connecting to application container..."
    docker-compose -f docker-compose.dev.yml exec web bash
}

# Status
status() {
    print_status "Development Service Status:"
    docker-compose -f docker-compose.dev.yml ps 2>/dev/null || echo "Development services not running"
    echo ""
    
    print_status "Production Service Status:"
    docker-compose ps 2>/dev/null || echo "Production services not running"
    echo ""
    
    if docker-compose -f docker-compose.dev.yml ps | grep -q "Up" || docker-compose ps | grep -q "Up"; then
        print_status "Testing web interface..."
        if curl -s http://localhost:5000/health > /dev/null 2>&1; then
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
    start-prod)
        start_prod
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
    test-gunicorn)
        test_gunicorn
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
