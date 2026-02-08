#!/bin/bash
# Setup script for Task Extraction System

set -e

echo "=================================================="
echo "Task Extraction System - Setup"
echo "=================================================="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check for PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL not found. Please install PostgreSQL 14+"
    exit 1
fi

echo "✅ PostgreSQL found"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for .env file
if [ ! -f .env ]; then
    echo ""
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY"
fi

# Setup database
echo ""
read -p "Do you want to setup the database now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Database name [task_extraction]: " DB_NAME
    DB_NAME=${DB_NAME:-task_extraction}
    
    echo ""
    echo "Creating database $DB_NAME..."
    createdb $DB_NAME 2>/dev/null || echo "Database already exists, continuing..."
    
    echo "Running schema..."
    psql -d $DB_NAME -f database.sql
    
    echo "Loading seed data..."
    psql -d $DB_NAME -f seed.sql
    
    echo "✅ Database setup complete!"
fi

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your AWS credentials:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - AWS_REGION (default: us-east-1)"
echo "   See AWS_SETUP.md for detailed configuration"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Test AWS Bedrock: python test_aws_bedrock.py"
echo "4. Run pipeline test: python test_pipeline.py"
echo "5. Start API: cd api && uvicorn main:app --reload"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""
