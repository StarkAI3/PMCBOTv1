#!/usr/bin/env python3
"""
PMC Chatbot Server
Serves both the FastAPI backend and HTML frontend
"""

import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sys

# Add the chatbot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'chatbot'))

# Import the chatbot API - using OpenAI version for correct embedding model
from chatbot_api_gpt4o import app as chatbot_app

# Create main app
app = FastAPI(title="PMC Chatbot", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the chatbot API
app.mount("/api", chatbot_app)

# Serve static files from templates directory
app.mount("/static", StaticFiles(directory="templates"), name="static")

@app.get("/")
async def read_index():
    """Serve the main HTML page"""
    return FileResponse("templates/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PMC Chatbot"}

if __name__ == "__main__":
    print("🚀 Starting PMC Chatbot Server...")
    print("📝 Make sure you have set up your .env file with:")
    print("   - OPENAI_API_KEY")
    print("   - PINECONE_API_KEY")
    print("   - PINECONE_INDEX")
    print("\n🌐 Server will be available at: http://localhost:8000")
    print("📱 Frontend: http://localhost:8000")
    print("🔌 API: http://localhost:8000/api")
    
    uvicorn.run(
        "run_chatbot_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 