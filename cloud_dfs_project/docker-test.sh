#!/bin/bash

# Docker Test Script for Distributed File System
# This script helps test both production and development Docker setups

set -e  # Exit on any error

echo "🐳 Docker Test Script for Distributed File System"
echo "=================================================="

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    echo "⏳ Waiting for $service_name to be ready..."
    for i in {1..30}; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $i/30: $service_name not ready yet, waiting 2s..."
        sleep 2
    done
    echo "❌ $service_name failed to become ready"
    return 1
}

# Function to test the application
test_application() {
    echo ""
    echo "🧪 Testing Application Endpoints"
    echo "================================"
    
    # Test health endpoint
    echo "Testing /health endpoint..."
    HEALTH_RESPONSE=$(curl -s http://localhost:5000/health)
    echo "Health Response: $HEALTH_RESPONSE"
    
    # Test main page
    echo "Testing main page..."
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/)
    echo "Main page HTTP Status: $HTTP_STATUS"
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "✅ Application is responding correctly!"
    else
        echo "❌ Application returned HTTP $HTTP_STATUS"
    fi
}

# Function to show container status
show_container_status() {
    echo ""
    echo "📊 Container Status"
    echo "==================="
    docker-compose ps
    echo ""
    echo "📈 Resource Usage"
    echo "=================="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Function to show logs
show_logs() {
    echo ""
    echo "📋 Recent Application Logs"
    echo "==========================="
    docker-compose logs web --tail=10
}

# Main menu
case "${1:-menu}" in
    "prod")
        echo "🚀 Testing Production Setup"
        echo "============================"
        
        # Clean up first
        docker-compose down --volumes || true
        
        # Build and start production
        echo "Building production images..."
        docker-compose build
        
        echo "Starting production containers..."
        docker-compose up -d
        
        # Wait for services
        wait_for_service "http://localhost:5000/health" "Web Application"
        
        # Test application
        test_application
        
        # Show status
        show_container_status
        show_logs
        
        echo ""
        echo "🎉 Production deployment test completed!"
        echo "🌐 Access your application at: http://localhost:5000"
        echo ""
        echo "📝 To stop: docker-compose down"
        echo "📝 To view logs: docker-compose logs web -f"
        ;;
        
    "dev")
        echo "🔧 Testing Development Setup"
        echo "============================="
        
        # Clean up first
        docker-compose -f docker-compose.dev.yml down --volumes || true
        
        # Build and start development
        echo "Building development images..."
        docker-compose -f docker-compose.dev.yml build
        
        echo "Starting development containers..."
        docker-compose -f docker-compose.dev.yml up -d
        
        # Wait for services
        wait_for_service "http://localhost:5000/health" "Web Application"
        
        # Test application
        test_application
        
        # Show status
        docker-compose -f docker-compose.dev.yml ps
        
        echo ""
        echo "🎉 Development deployment test completed!"
        echo "🌐 Access your application at: http://localhost:5000"
        echo "🔄 Development mode: Code changes will auto-reload"
        echo ""
        echo "📝 To stop: docker-compose -f docker-compose.dev.yml down"
        ;;
        
    "stop")
        echo "🛑 Stopping all containers..."
        docker-compose down || true
        docker-compose -f docker-compose.dev.yml down || true
        echo "✅ All containers stopped"
        ;;
        
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        docker-compose down --volumes --rmi all || true
        docker-compose -f docker-compose.dev.yml down --volumes --rmi all || true
        docker system prune -f
        echo "✅ Cleanup completed"
        ;;
        
    "status")
        echo "📊 Current Status"
        echo "=================="
        echo "Production containers:"
        docker-compose ps || echo "No production containers running"
        echo ""
        echo "Development containers:"
        docker-compose -f docker-compose.dev.yml ps || echo "No development containers running"
        ;;
        
    "logs")
        echo "📋 Application Logs"
        echo "==================="
        if docker-compose ps | grep -q "dfs_web.*Up"; then
            echo "Production logs:"
            docker-compose logs web --tail=20
        elif docker-compose -f docker-compose.dev.yml ps | grep -q "dfs_web_dev.*Up"; then
            echo "Development logs:"
            docker-compose -f docker-compose.dev.yml logs web --tail=20
        else
            echo "No containers running"
        fi
        ;;
        
    *)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  prod    - Test production deployment"
        echo "  dev     - Test development deployment"
        echo "  stop    - Stop all containers"
        echo "  clean   - Clean up all Docker resources"
        echo "  status  - Show container status"
        echo "  logs    - Show recent logs"
        echo ""
        echo "Examples:"
        echo "  ./docker-test.sh prod    # Test production setup"
        echo "  ./docker-test.sh dev     # Test development setup"
        echo "  ./docker-test.sh status  # Check what's running"
        ;;
esac
