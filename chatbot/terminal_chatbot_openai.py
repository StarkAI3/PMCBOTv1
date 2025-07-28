import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone
import openai
from langdetect import detect
import re
from collections import deque

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_INDEX = os.getenv('PINECONE_INDEX', 'pmc-bot-index')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize Pinecone and OpenAI
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)
openai.api_key = OPENAI_API_KEY

# Settings
TOP_K = 5
CONTEXT_RESULTS = 3  # Number of Pinecone results to pass to LLM
MAX_HISTORY = 2      # Number of previous turns to include

# Use the same embedding model as used for indexing
EMBEDDING_MODEL = 'text-embedding-3-small'  # or 'text-embedding-3-large'
LLM_MODEL = 'gpt-4o'  # or 'gpt-4o-mini' for cost optimization

# Keywords for 'recent/latest' intent
def is_latest_query(query):
    LATEST_KEYWORDS = [
        r"latest", r"most recent", r"newest", r"recent", r"last", r"current", r"today(?:'s)?", r"this week", r"fresh", r"updated", r"up-to-date", r"just published", r"just released", r"recently issued", r"recently published", r"recently released"
    ]
    pattern = re.compile(r"|".join(LATEST_KEYWORDS), re.IGNORECASE)
    return bool(pattern.search(query))

def is_followup_query(query, prev_user_query):
    pronouns = ["it", "that", "this", "one", "which", "above", "them", "those", "these"]
    q_lower = query.lower().strip()
    # If no previous user query, can't be a follow-up
    if not prev_user_query:
        return False
    # If query is very short and contains a pronoun, likely a follow-up
    if len(q_lower.split()) <= 6 and any(p in q_lower for p in pronouns):
        return True
    # If query is a full question (starts with 'which', 'what', etc.) and is long enough, treat as standalone
    question_words = ["which", "what", "where", "who", "when", "how"]
    if any(q_lower.startswith(w) for w in question_words) and len(q_lower.split()) > 6:
        return False
    # Default: not a follow-up
    return False

# Helper: Detect language
def detect_language(text):
    try:
        lang = detect(text)
        if lang == 'mr':
            return 'mr'
        return 'en'
    except Exception:
        return 'en'

# Helper: Embed query using OpenAI
def embed_query(text):
    """Embed query using OpenAI embeddings for consistency with indexed data"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
            encoding_format='float'
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

# Helper: Format Pinecone results for LLM context (with links)
def format_pinecone_results(docs):
    formatted = []
    for i, doc in enumerate(docs, 1):
        meta = doc.get('metadata', {})
        title = meta.get('title', '')
        description = meta.get('description', '')
        date = meta.get('date', meta.get('display_date', ''))
        department = meta.get('department', '')
        ward_name = meta.get('ward_name', '')
        record_type = meta.get('record_type', '')
        
        # Prefer PDF, then external, then url
        link = meta.get('pdf_url') or meta.get('external_link') or meta.get('url')
        
        s = f"Record {i}:\n"
        if title:
            s += f"Title: {title}\n"
        if description:
            s += f"Description: {description}\n"
        if date:
            s += f"Date: {date}\n"
        if department:
            s += f"Department: {department}\n"
        if ward_name:
            s += f"Ward: {ward_name}\n"
        if record_type and record_type != 'other':
            s += f"Type: {record_type}\n"
        if link:
            s += f"Link: {link}\n"
        formatted.append(s.strip())
    return '\n---\n'.join(formatted)

# Helper: Build LLM prompt
def build_llm_prompt(user_query, pinecone_context, chat_history, lang):
    # Language-specific instructions
    if lang == 'mr':
        language_instruction = "Please respond in Marathi (मराठी) language."
    else:
        language_instruction = "Please respond in English language."
    
    prompt = f"""You are a helpful assistant for Pune Municipal Corporation (PMC) information. You have access to PMC's official records and documents.

User Query:
{user_query}

Relevant Information from PMC Database:
{pinecone_context}

{language_instruction}

Instructions:
- Carefully read all the records above and answer the user's query in a clear, friendly, and human-like manner.
- If the information is not available in the provided records, clearly state that you don't have that specific information.
- Always provide accurate information based on the PMC records.
- Include relevant links when available.
- Be helpful and professional in your responses.
- If the user asks about recent or latest information, prioritize records with more recent dates.
- For location-specific queries, mention the relevant ward or department information.
- If the query is in Marathi, respond in Marathi. If in English, respond in English.

Please provide a comprehensive answer based on the available information."""

    if chat_history:
        prompt += "\n\nPrevious Conversation Context:\n"
        for turn in chat_history:
            # Handle both dictionary and object formats
            if hasattr(turn, 'user') and hasattr(turn, 'bot'):
                # ChatHistoryItem object
                prompt += f"User: {turn.user}\nBot: {turn.bot}\n"
            elif isinstance(turn, dict):
                # Dictionary format
                prompt += f"User: {turn['user']}\nBot: {turn['bot']}\n"
    
    return prompt

# Helper: Generate response using OpenAI GPT
def generate_response(prompt):
    """Generate response using OpenAI GPT model"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for Pune Municipal Corporation (PMC) information."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Generation error: {e}")
        return "I apologize, but I'm having trouble generating a response right now. Please try again."

# Helper: Replace URL markdown with "here"
def replace_url_markdown_with_here(text):
    # Replace [URL](URL) with [here](URL)
    import re
    def replacer(match):
        url = match.group(1)
        return f"[here]({url})"
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, text)

# Helper: Remove duplicate links
def remove_duplicate_links(text):
    # Simple deduplication of URLs
    import re
    def url_replacer(match):
        url = match.group(1)
        if url in seen_urls:
            return ""
        seen_urls.add(url)
        return match.group(0)
    
    seen_urls = set()
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', url_replacer, text)

# Helper: Validate and fix markdown links
def validate_and_fix_markdown_links(text):
    # Fix common markdown link issues
    import re
    def replacer(match):
        text_part = match.group(1)
        url_part = match.group(2)
        # Clean up the URL
        url_part = url_part.strip()
        if not url_part.startswith(('http://', 'https://')):
            url_part = 'https://' + url_part
        return f"[{text_part}]({url_part})"
    
    # Fix markdown links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, text)
    return text

def main():
    """Main chat loop"""
    print(f"PMC Chatbot - Using {LLM_MODEL} for generation and {EMBEDDING_MODEL} for search")
    print("Type 'quit' to exit")
    print("-" * 50)
    
    chat_history = deque(maxlen=MAX_HISTORY)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Language detection
            lang = detect_language(user_input)
            
            # Follow-up handling
            prev_user_query = chat_history[-1]['user'] if chat_history else None
            query_for_search = user_input
            if is_followup_query(user_input, prev_user_query):
                query_for_search = f"{user_input.strip()} (context: {prev_user_query})"
            
            # Embed and search Pinecone
            query_emb = embed_query(query_for_search)
            if not query_emb:
                print("Error: Could not embed query. Please try again.")
                continue
            
            results = index.query(vector=query_emb, top_k=TOP_K, include_metadata=True)
            docs = results.get('matches', [])
            
            # If 'recent/latest' intent, sort by date
            if is_latest_query(user_input):
                def parse_date_safe(meta):
                    d = meta.get('metadata', {})
                    return d.get('date') or d.get('display_date') or ''
                docs = sorted(docs, key=parse_date_safe, reverse=True)
            
            # Use top N results for context
            context_docs = docs[:CONTEXT_RESULTS]
            pinecone_context = format_pinecone_results(context_docs) if context_docs else "No relevant information found."
            
            # Build prompt and generate response
            prompt = build_llm_prompt(user_input, pinecone_context, list(chat_history), lang)
            answer = generate_response(prompt)
            
            # Clean up the response
            answer = remove_duplicate_links(answer)
            answer = validate_and_fix_markdown_links(answer)
            
            print(f"\nBot: {answer}")
            
            # Update chat history
            chat_history.append({'user': user_input, 'bot': answer})
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == '__main__':
    main() 