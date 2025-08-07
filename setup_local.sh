#!/bin/bash

# Setup local development environment for ShadowBeta Financial Dashboard
echo "🚀 Setting up ShadowBeta Financial Dashboard..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if Yarn is installed
if ! command -v yarn &> /dev/null; then
    echo "❌ Yarn is not installed. Please install Yarn first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install backend dependencies"
    exit 1
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd ../frontend
yarn install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi

# Create .env file for backend
echo "⚙️ Creating backend environment file..."
cd ../backend
if [ ! -f .env ]; then
    cat > .env << EOF
# ShadowBeta Financial Dashboard Environment Configuration

# Database Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=shadowbeta

# Required API Keys (Get these from the respective services)
FINNHUB_API_KEY=your_finnhub_key_here
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional Features
DISCORD_TOKEN=your_discord_token_here
CHANNEL_ID=your_channel_id_here
NEWS_API_KEY=your_news_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
EOF
    echo "✅ Created .env file in backend directory"
    echo "⚠️  Please update the .env file with your actual API keys"
else
    echo "✅ .env file already exists"
fi

# Create .env file for frontend
echo "⚙️ Creating frontend environment file..."
cd ../frontend
if [ ! -f .env ]; then
    cat > .env << EOF
# ShadowBeta Frontend Environment Configuration
REACT_APP_BACKEND_URL=http://localhost:8000
WDS_SOCKET_PORT=443
EOF
    echo "✅ Created .env file in frontend directory"
else
    echo "✅ .env file already exists"
fi

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update the backend/.env file with your API keys"
echo "2. Start MongoDB (if not already running)"
echo "3. Start the backend: cd backend && python server.py"
echo "4. Start the frontend: cd frontend && yarn start"
echo ""
echo "🌐 The application will be available at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo ""
echo "📚 For more information, see the README.md file"
