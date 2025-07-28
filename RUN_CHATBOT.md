# 🚀 PMC Chatbot - Quick Start Guide

## Overview
This is a multilingual chatbot for Pune Municipal Corporation (PMC) that provides information about PMC services, documents, and procedures. It supports both English and Marathi languages.

## Features
- 🌐 **Web Interface**: Modern chat UI
- 🌍 **Multilingual**: English and Marathi support
- 🔍 **Semantic Search**: Powered by Pinecone vector database
- 🤖 **AI-Powered**: Uses OpenAI GPT-4o for intelligent responses
- 📚 **Rich Context**: Access to PMC documents and information

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the project root with:
```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone Configuration  
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX=pmc-bot-index
PINECONE_ENV=us-east-1-aws

# Optional: Gemini API (if you want to switch to Gemini later)
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Verify Setup
```bash
python setup_chatbot.py
```

### 4. Start the Server
```bash
python run_chatbot_server.py
```

### 5. Open in Browser
Navigate to: **http://localhost:8000**

## API Endpoints

- **Frontend**: `http://localhost:8000/`
- **Chat API**: `http://localhost:8000/api/chat`
- **Health Check**: `http://localhost:8000/health`

## Usage Examples

### English Queries
- "How do I pay property tax?"
- "What documents do I need for building permission?"
- "Show me the latest PMC circulars"

### Marathi Queries
- "मालमत्ता कर कसा भरायचा?"
- "बांधकाम परवानगीसाठी कोणते कागदपत्रे लागतात?"
- "सर्वात नवीन PMC परिपत्रके दाखवा"

## Troubleshooting

### Common Issues

1. **Missing API Keys**
   - Ensure your `.env` file has valid API keys
   - Check that your OpenAI and Pinecone accounts are active

2. **Pinecone Index Not Found**
   - Verify your Pinecone index name in `.env`
   - Make sure the index exists and is accessible

3. **Port Already in Use**
   - Change the port in `run_chatbot_server.py`
   - Or kill the process using port 8000

4. **Import Errors**
   - Activate your virtual environment
   - Run `pip install -r requirements.txt`

### Getting Help
- Run `python setup_chatbot.py` to diagnose issues
- Check the console output for error messages
- Verify all environment variables are set correctly

## Architecture

```
Frontend (index.html)
    ↓
FastAPI Server (run_chatbot_server.py)
    ↓
Chatbot API (chatbot_api_gpt4o.py)
    ↓
OpenAI GPT-4o + Pinecone Vector DB
```

## Data Sources
The chatbot uses data from:
- PMC official documents
- Service information
- Circulars and notices
- Department-wise information

All data is embedded and stored in Pinecone for semantic search. 