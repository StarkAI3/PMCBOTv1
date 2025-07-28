#!/usr/bin/env python3
"""
PMC Chatbot Setup Script
Helps configure and verify the chatbot setup
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("\n📝 Please create a .env file with the following variables:")
        print("""
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_placeholder

# Pinecone Configuration  
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX=pmc-bot-index
PINECONE_ENV=us-east-1-aws

# Optional: Gemini API (if you want to switch to Gemini later)
GEMINI_API_KEY=your_gemini_api_key_here
        """)
        return False
    
    print("✅ .env file found")
    
    # Check if required variables are set
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['OPENAI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_INDEX']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    print("\n🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'openai', 'pinecone', 
        'python-dotenv', 'langdetect', 'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies are installed")
    return True

def check_data_files():
    """Check if data files exist"""
    print("\n📁 Checking data files...")
    
    data_files = [
        'data/pmc_data_normalized.jsonl',
        'templates/index.html',
        'chatbot/chatbot_api_gpt4o.py',
        'chatbot/terminal_chatbot_v2.py'
    ]
    
    missing_files = []
    
    for file_path in data_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - not found")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files are present")
    return True

def test_pinecone_connection():
    """Test Pinecone connection"""
    print("\n🌲 Testing Pinecone connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        
        # List indexes
        indexes = pc.list_indexes()
        index_name = os.getenv('PINECONE_INDEX')
        
        if any(idx.name == index_name for idx in indexes):
            print(f"✅ Pinecone index '{index_name}' found")
            
            # Test index connection
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            print(f"✅ Index stats: {stats.total_vector_count} vectors")
            return True
        else:
            print(f"❌ Pinecone index '{index_name}' not found")
            print("Available indexes:", [idx.name for idx in indexes])
            return False
            
    except Exception as e:
        print(f"❌ Pinecone connection failed: {e}")
        return False

def main():
    print("🚀 PMC Chatbot Setup Check")
    print("=" * 50)
    
    checks = [
        check_env_file,
        check_dependencies,
        check_data_files,
        test_pinecone_connection
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All checks passed! Your chatbot is ready to run.")
        print("\n🚀 To start the chatbot server:")
        print("   python run_chatbot_server.py")
        print("\n🌐 Then open your browser to: http://localhost:8000")
    else:
        print("❌ Some checks failed. Please fix the issues above before running the chatbot.")
        print("\n💡 Common solutions:")
        print("1. Create .env file with your API keys")
        print("2. Install missing packages: pip install -r requirements.txt")
        print("3. Make sure your Pinecone index exists and is accessible")

if __name__ == "__main__":
    main() 