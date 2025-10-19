#!/bin/bash
# Quick deployment script for VectorDB-Q

set -e

echo "🚀 VectorDB-Q Docker Deployment"
echo "================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "   Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your Cohere API key!"
    echo "   COHERE_API_KEY=your_actual_key_here"
    echo ""
    read -p "Press Enter after updating .env file..."
fi

# Check if Cohere API key is set
if grep -q "your_cohere_api_key_here" .env; then
    echo "⚠️  WARNING: You haven't set your Cohere API key in .env"
    echo "   The application won't work without it!"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "📦 Building Docker image..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check health
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ Service is healthy!"
    echo ""
    echo "🎉 Deployment successful!"
    echo ""
    echo "📍 Access your application:"
    echo "   Frontend:    http://localhost:8000/"
    echo "   API Docs:    http://localhost:8000/docs"
    echo "   Health:      http://localhost:8000/health"
    echo ""
    echo "📋 Useful commands:"
    echo "   docker-compose logs -f       # View logs"
    echo "   docker-compose restart       # Restart services"
    echo "   docker-compose down          # Stop services"
    echo ""
else
    echo "⚠️  Service is not responding yet"
    echo "   Check logs: docker-compose logs -f"
    echo ""
fi
