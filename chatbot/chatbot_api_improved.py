from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional, Dict
from collections import deque
from fastapi.middleware.cors import CORSMiddleware
import openai
import os
import re
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
import uuid

# Import improved functions
from terminal_chatbot_openai_improved import (
    detect_language, is_followup_query, is_latest_query, embed_query, 
    index, TOP_K, CONTEXT_RESULTS, format_pinecone_results, 
    build_llm_prompt, remove_duplicate_links, parse_date_safe
)

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatHistoryItem(BaseModel):
    user: str
    bot: str

class ChatRequest(BaseModel):
    user_input: str
    history: Optional[List[ChatHistoryItem]] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PMC Chatbot (Improved)"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        print("[INFO] Received /chat request")
        print(f"[INFO] Request data: {request}")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        user_input = request.user_input.strip()
        history = deque(request.history or [], maxlen=2)
        # Handle both ChatHistoryItem objects and plain dictionaries
        prev_user_query = None
        if history:
            last_item = history[-1]
            if hasattr(last_item, 'user'):
                prev_user_query = last_item.user
            elif isinstance(last_item, dict):
                prev_user_query = last_item.get('user')
        lang = detect_language(user_input)
        
        # Enhanced query processing
        query_for_search = user_input
        is_followup = is_followup_query(user_input, prev_user_query)
        if is_followup:
            query_for_search = f"{user_input.strip()} (context: {prev_user_query})"
            print(f"[INFO] Detected follow-up query. Original: '{user_input}', Enhanced: '{query_for_search}'")
        else:
            print(f"[INFO] Regular query: '{user_input}'")
        
        # Embed and search with improved parameters
        query_emb = embed_query(query_for_search)
        if not query_emb:
            return ChatResponse(answer="I apologize, but I'm having trouble processing your query right now. Please try again.")
        
        results = index.query(vector=query_emb, top_k=TOP_K, include_metadata=True)
        docs = results.get('matches', [])
        
        # Enhanced sorting for latest queries
        if is_latest_query(user_input):
            def safe_date_sort(doc):
                date_str = doc.metadata.get('date', doc.metadata.get('display_date', ''))
                return parse_date_safe(date_str)
            docs = sorted(docs, key=safe_date_sort, reverse=True)
        
        # Use more context for better responses
        context_docs = docs[:CONTEXT_RESULTS]
        pinecone_context = format_pinecone_results(context_docs) if context_docs else "No relevant information found."
        
        # Convert history to the format expected by build_llm_prompt
        chat_history = []
        for item in history:
            if hasattr(item, 'user') and hasattr(item, 'bot'):
                chat_history.append({'user': item.user, 'bot': item.bot})
            elif isinstance(item, dict):
                chat_history.append(item)
        
        print(f"[INFO] Chat history length: {len(chat_history)}")
        if chat_history:
            print(f"[INFO] Previous user query: '{prev_user_query}'")
            print(f"[INFO] History items: {[(h.get('user', '')[:50] + '...' if len(h.get('user', '')) > 50 else h.get('user', '')) for h in chat_history]}")
        
        prompt = build_llm_prompt(user_input, pinecone_context, chat_history, lang)
        
        print(f"[INFO] Prompt sent to OpenAI:\n{prompt}")
        
        # Generate answer using OpenAI GPT-4o
        system_message = """You are a helpful assistant for Pune Municipal Corporation (PMC) information. 
You have access to PMC's official records and documents. When users ask follow-up questions, 
always check the previous conversation context first before searching the PMC records. 
If the information is available in the previous conversation, use it to answer the follow-up question."""
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message}, 
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
            temperature=0.2
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"[INFO] OpenAI answer: {answer}")
        
        # Clean up the response
        answer = remove_duplicate_links(answer)
        
        return ChatResponse(answer=answer, session_id=session_id)
        
    except Exception as e:
        import traceback
        print("[ERROR] Exception in /chat endpoint:")
        traceback.print_exc()
        return ChatResponse(answer=f"I apologize, but I encountered an error while processing your request. Please try again.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 