# PMC Chatbot - Pune Municipal Corporation AI Assistant

A comprehensive multilingual chatbot system for the Pune Municipal Corporation (PMC) that provides intelligent responses to citizen queries in both English and Marathi. The system uses advanced AI technologies including OpenAI GPT-4o for natural language processing and Pinecone vector database for semantic search.

## 🌟 Features

### Core Capabilities
- **🌐 Multilingual Support**: Full support for English and Marathi languages
- **🤖 AI-Powered Responses**: Uses OpenAI GPT-4o for intelligent, contextual answers
- **🔍 Semantic Search**: Advanced vector search using Pinecone for relevant information retrieval
- **📱 Web Interface**: Modern, responsive chat UI accessible via browser
- **💻 Terminal Interface**: Command-line chatbot for developers and testing
- **📊 Rich Data Integration**: Access to comprehensive PMC documents, circulars, and services

### Advanced Features
- **Context-Aware Conversations**: Maintains conversation context for follow-up queries
- **Latest Information Detection**: Automatically prioritizes recent documents and updates
- **Smart Query Classification**: Intelligent categorization of user intent
- **Link Management**: Automatic detection and formatting of relevant URLs
- **Error Handling**: Robust error handling and graceful degradation

## 🏗️ Project Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   FastAPI Server │    │  OpenAI GPT-4o  │
│   (index.html)  │◄──►│ (run_chatbot_    │◄──►│   + Pinecone    │
│                 │    │   server.py)     │    │   Vector DB     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Data Pipeline  │
                       │  (Scripts/)     │
                       └──────────────────┘
```

## 📁 Project Structure

```
PMC-BOT-/
├── chatbot/                          # Chatbot implementation files
│   ├── chatbot_api_gpt4o.py         # FastAPI chatbot endpoint
│   ├── terminal_chatbot_openai.py    # Terminal-based chatbot
│   ├── terminal_chatbot_gpt4o.py    # GPT-4o terminal chatbot
│   └── terminal_chatbot_v2.py       # Enhanced terminal version
├── scripts/                          # Data processing scripts
│   ├── normalize_pmc_data.py         # Data normalization and cleaning
│   ├── embed_and_upsert_openai.py   # OpenAI embedding generation
│   ├── embed_and_upsert.py          # Legacy embedding script
│   ├── create_pinecone_index.py     # Pinecone index creation
│   ├── clear_pinecone_index.py      # Index management utility
│   └── enhanced_extract_pmc_data.py # Enhanced data extraction
├── templates/                        # Web interface files
│   └── index.html                   # Chatbot web interface
├── data/                            # Processed PMC data
├── run_chatbot_server.py            # Main server entry point
├── setup_chatbot.py                 # Setup and verification script
├── requirements.txt                  # Python dependencies
├── .env                             # Environment variables (create this)
└── README.md                        # This file
```

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- Pinecone API key
- Internet connection

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone https://github.com/your-username/PMC-BOT-.git
cd PMC-BOT-

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment
Create a `.env` file in the project root:
```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone Configuration  
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX=pmc-bot-index
PINECONE_ENV=us-east-1-aws

# Optional: Gemini API (for legacy support)
GEMINI_API_KEY=your_gemini_api_key_here
```

### Step 3: Verify Setup
```bash
python setup_chatbot.py
```

### Step 4: Start the Chatbot
```bash
# Start the web server
python run_chatbot_server.py
```

### Step 5: Access the Chatbot
Open your browser and navigate to: **http://localhost:8000**

## 🔧 Detailed Setup Instructions

### 1. API Key Setup

#### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Add to your `.env` file

#### Pinecone API Key
1. Visit [Pinecone Console](https://app.pinecone.io/)
2. Create an account or sign in
3. Create a new project
4. Generate an API key
5. Add to your `.env` file

### 2. Data Setup

The project includes pre-processed PMC data, but you can regenerate it:

```bash
# Normalize and clean PMC data
python scripts/normalize_pmc_data.py

# Create Pinecone index
python scripts/create_pinecone_index.py

# Generate embeddings and upload to Pinecone
python scripts/embed_and_upsert_openai.py
```

### 3. Index Configuration

Recommended Pinecone settings:
- **Index Name**: `pmc-bot-index`
- **Dimensions**: 1536 (for `text-embedding-3-small`) or 3072 (for `text-embedding-3-large`)
- **Metric**: cosine
- **Type**: Dense
- **Capacity Mode**: Serverless
- **Cloud**: AWS
- **Region**: us-east-1

## 🎯 Usage Examples

### Web Interface
1. Start the server: `python run_chatbot_server.py`
2. Open browser to `http://localhost:8000`
3. Type your questions in English or Marathi

### Terminal Interface
```bash
# Start terminal chatbot
python chatbot/terminal_chatbot_openai.py

# Example queries:
# English: "How do I pay property tax?"
# Marathi: "मालमत्ता कर कसा भरायचा?"
```

### API Usage
```bash
# Health check
curl http://localhost:8000/health

# Chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_input": "How do I get building permission?"}'
```

## 📊 Data Processing Pipeline

### 1. Data Extraction (`enhanced_extract_pmc_data.py`)
- Extracts data from PMC sources
- Handles both English and Marathi content
- Processes various document types

### 2. Data Normalization (`normalize_pmc_data.py`)
- Cleans and standardizes data
- Extracts comprehensive content from all fields
- Classifies documents into meaningful categories
- Handles HTML content cleaning
- Preserves multilingual support

### 3. Embedding Generation (`embed_and_upsert_openai.py`)
- Generates OpenAI embeddings for semantic search
- Chunks large documents intelligently
- Uploads to Pinecone vector database
- Maintains metadata for context

### 4. Search and Response (`chatbot_api_gpt4o.py`)
- Processes user queries
- Performs semantic search
- Generates contextual responses
- Handles conversation flow

## 🔍 Query Types Supported

### English Queries
- **Service Information**: "How do I pay property tax?"
- **Document Requirements**: "What documents do I need for building permission?"
- **Latest Updates**: "Show me the latest PMC circulars"
- **Location-based**: "Hospital facilities in ward 15"
- **Department-specific**: "Contact information for electrical department"

### Marathi Queries
- **सेवा माहिती**: "मालमत्ता कर कसा भरायचा?"
- **कागदपत्रे**: "बांधकाम परवानगीसाठी कोणते कागदपत्रे लागतात?"
- **नवीन माहिती**: "सर्वात नवीन PMC परिपत्रके दाखवा"
- **स्थानिक**: "वॉर्ड 15 मधील रुग्णालय सुविधा"
- **विभागीय**: "विद्युत विभागाची संपर्क माहिती"

## 🛠️ Development and Customization

### Adding New Data Sources
1. Add data extraction script in `scripts/`
2. Update normalization script to handle new format
3. Re-run embedding generation
4. Test with chatbot

### Modifying Response Logic
1. Edit `chatbot/chatbot_api_gpt4o.py`
2. Modify prompt engineering in `build_llm_prompt()`
3. Adjust search parameters in `TOP_K` and `CONTEXT_RESULTS`

### Customizing UI
1. Modify `templates/index.html`
2. Update CSS styles for different appearance
3. Add new JavaScript functionality as needed

## 🔧 Troubleshooting

### Common Issues

#### 1. Missing API Keys
```bash
# Check environment variables
python setup_chatbot.py
```
**Solution**: Ensure all API keys are set in `.env` file

#### 2. Pinecone Index Not Found
```bash
# Check available indexes
python scripts/create_pinecone_index.py
```
**Solution**: Create index or update `PINECONE_INDEX` in `.env`

#### 3. Port Already in Use
```bash
# Change port in run_chatbot_server.py
uvicorn.run("run_chatbot_server:app", host="0.0.0.0", port=8001)
```
**Solution**: Use different port or kill existing process

#### 4. Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```
**Solution**: Ensure virtual environment is activated

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python run_chatbot_server.py
```

## 📈 Performance Optimization

### Cost Optimization
- Use `gpt-4o-mini` instead of `gpt-4o` for lower costs
- Use `text-embedding-3-small` instead of `text-embedding-3-large`
- Implement caching for frequent queries

### Speed Optimization
- Reduce `TOP_K` value for faster search
- Implement response caching
- Use async processing for multiple queries

### Accuracy Improvement
- Increase `TOP_K` for more comprehensive search
- Use `text-embedding-3-large` for better embeddings
- Fine-tune prompt engineering

## 🔒 Security Considerations

### API Key Security
- Never commit API keys to version control
- Use environment variables for sensitive data
- Rotate API keys regularly

### Data Privacy
- Ensure compliance with local data protection laws
- Implement user data anonymization if needed
- Regular security audits

## 📚 API Documentation

### Endpoints

#### `GET /health`
Health check endpoint
```json
{
  "status": "healthy",
  "service": "PMC Chatbot"
}
```

#### `POST /api/chat`
Main chat endpoint
```json
{
  "user_input": "How do I pay property tax?",
  "history": [
    {
      "user": "What are the tax rates?",
      "bot": "The property tax rates are..."
    }
  ]
}
```

Response:
```json
{
  "answer": "To pay property tax, you can..."
}
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit pull request with detailed description

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Include docstrings for functions

### Testing
```bash
# Run setup verification
python setup_chatbot.py

# Test chatbot functionality
python chatbot/terminal_chatbot_openai.py
```

## 📄 License

This project is for educational and research purposes. Please ensure compliance with OpenAI and Pinecone terms of service.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4o and embedding models
- **Pinecone** for vector database services
- **Pune Municipal Corporation** for data sources
- **FastAPI** for web framework
- **BeautifulSoup** for HTML processing

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review existing documentation
3. Create an issue on GitHub with detailed description
4. Include error messages and system information

---

**Note**: This chatbot is designed to provide information about PMC services and should not be used for official legal or administrative purposes. Always verify information with official PMC sources. 