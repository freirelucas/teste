#!/bin/bash
# Overton Analyzer - Run Script

echo "🔬 Starting Overton Policy Citation Analyzer..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copy .env.example to .env and add your API key."
    echo "   You can also enter the API key in the web interface."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting application..."
echo "   Access the web interface at: http://localhost:5000"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""

# Run the application
python app.py
