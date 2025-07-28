#!/usr/bin/env python3
"""
PMC Chatbot Server (Improved)
Serves both the FastAPI backend and HTML frontend with enhanced functionality
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

# Import the improved chatbot API
from chatbot_api_improved import app as chatbot_app

# Create main app
app = FastAPI(title="PMC Chatbot (Improved)", version="2.0.0")

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
    return {"status": "healthy", "service": "PMC Chatbot (Improved)", "version": "2.0.0"}

if __name__ == "__main__":
    print("🚀 Starting PMC Chatbot Server (Improved)...")
    print("📝 Make sure you have set up your .env file with:")
    print("   - OPENAI_API_KEY")
    print("   - PINECONE_API_KEY")
    print("   - PINECONE_INDEX")
    print("\n🔧 Improvements in this version:")
    print("   ✅ Better link validation (no invalid URLs)")
    print("   ✅ Enhanced latest circular detection")
    print("   ✅ Improved date sorting")
    print("   ✅ Better context handling")
    print("\n🌐 Server will be available at: http://localhost:8000")
    print("📱 Frontend: http://localhost:8000")
    print("🔌 API: http://localhost:8000/api")
    
    uvicorn.run(
        "run_chatbot_server_improved:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 