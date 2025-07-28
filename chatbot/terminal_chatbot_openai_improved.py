import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone
import openai
from langdetect import detect
import re
from collections import deque
from datetime import datetime
from urllib.parse import urlparse

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
TOP_K = 15  # Increased for better search
CONTEXT_RESULTS = 8 # Increased for better context
MAX_HISTORY = 5

# Use the same embedding model as used for indexing
EMBEDDING_MODEL = 'text-embedding-3-small'
LLM_MODEL = 'gpt-4o'

def is_latest_query(query):
    """Enhanced latest query detection"""
    LATEST_KEYWORDS = [
        r"latest", r"most recent", r"newest", r"recent", r"last", r"current", 
        r"today(?:'s)?", r"this week", r"fresh", r"updated", r"up-to-date", 
        r"just published", r"just released", r"recently issued", r"recently published", 
        r"recently released", r"latest circular", r"recent circular", r"new circular"
    ]
    pattern = re.compile(r"|".join(LATEST_KEYWORDS), re.IGNORECASE)
    return bool(pattern.search(query))

def is_followup_query(query, prev_user_query):
    """Enhanced follow-up detection"""
    pronouns = ["it", "that", "this", "one", "which", "above", "them", "those", "these"]
    q_lower = query.lower().strip()
    
    if not prev_user_query:
        return False
    
    # Check for pronouns in short queries
    if len(q_lower.split()) <= 6 and any(p in q_lower for p in pronouns):
        return True
    
    # Check for references to previous content
    reference_patterns = [
        r"from above",
        r"from the list", 
        r"from those",
        r"which one",
        r"nearest to me",
        r"closest to me",
        r"near me",
        r"nearby",
        r"the one",
        r"that one",
        r"this one"
    ]
    
    for pattern in reference_patterns:
        if re.search(pattern, q_lower):
            return True
    
    # Check for specific follow-up patterns
    followup_patterns = [
        r"what is the date",
        r"when was it",
        r"where is it",
        r"who issued it",
        r"which department",
        r"what about",
        r"tell me more",
        r"give me details",
        r"what else",
        r"any other",
        r"is there more",
        r"which one",
        r"from above",
        r"from the list",
        r"from those",
        r"nearest to me",
        r"closest to me",
        r"near me",
        r"nearby"
    ]
    
    for pattern in followup_patterns:
        if re.search(pattern, q_lower):
            return True
    
    # Check for question words with context-dependent queries
    question_words = ["which", "what", "where", "who", "when", "how"]
    if any(q_lower.startswith(w) for w in question_words):
        # If it's a short question, likely a follow-up
        if len(q_lower.split()) <= 4:
            return True
        # If it's longer but contains context-dependent words
        context_words = ["date", "time", "location", "department", "ward", "circular", "notice", 
                        "place", "places", "nearest", "closest", "near", "nearby", "distance", 
                        "area", "region", "zone", "above", "list", "those", "one"]
        if any(word in q_lower for word in context_words):
            return True
    
    return False

def detect_language(text):
    """Language detection"""
    try:
        lang = detect(text)
        if lang == 'mr':
            return 'mr'
        return 'en'
    except Exception:
        return 'en'

def embed_query(text):
    """Embed query using OpenAI embeddings"""
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

def validate_url(url):
    """Validate and fix URLs"""
    if not url:
        return None
    
    # Skip relative URLs and internal IPs
    if url.startswith('/') or url.startswith('http://115.124.97.169'):
        return None
    
    # Ensure proper protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Basic URL validation
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return url
    except:
        pass
    
    return None

def format_pinecone_results(docs):
    """Enhanced formatting with URL validation"""
    formatted = []
    for i, doc in enumerate(docs, 1):
        meta = doc.get('metadata', {})
        title = meta.get('title', '')
        description = meta.get('description', '')
        date = meta.get('date', meta.get('display_date', ''))
        department = meta.get('department', '')
        ward_name = meta.get('ward_name', '')
        record_type = meta.get('record_type', '')
        
        # Get and validate link
        link = meta.get('pdf_url') or meta.get('external_link') or meta.get('url')
        valid_link = validate_url(link)
        
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
        if valid_link:
            s += f"Link: {valid_link}\n"
        formatted.append(s.strip())
    return '\n---\n'.join(formatted)

def parse_date_safe(date_str):
    """Enhanced date parsing that returns consistent string format for sorting"""
    if not date_str:
        return ''
    
    # Try to parse various date formats
    date_formats = [
        '%d %B %Y', '%d %b %Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y',
        '%d-%m-%Y', '%Y/%m/%d', '%B %d, %Y', '%b %d, %Y'
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            # Return in YYYY-MM-DD format for consistent string sorting
            return parsed_date.strftime('%Y-%m-%d')
        except:
            continue
    
    # If no format matches, return the original string for sorting
    return date_str

def build_llm_prompt(user_query, pinecone_context, chat_history, lang):
    """Enhanced prompt building"""
    if lang == 'mr':
        language_instruction = "Please respond in Marathi (मराठी) language."
    else:
        language_instruction = "Please respond in English language."
    
    # Enhanced instructions for better link handling
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
- Only include links that are valid and accessible (https:// URLs only).
- Do not include relative URLs (starting with /) or internal IP addresses.
- If a link is invalid, mention the information without the link.
- Be helpful and professional in your responses.
- If the user asks about recent or latest information, prioritize records with more recent dates.
- For location-specific queries, mention the relevant ward or department information.
- If the query is in Marathi, respond in Marathi. If in English, respond in English.
- When asked about "latest" or "recent" circulars, focus on the most recent dated records.

Please provide a comprehensive answer based on the available information."""

    if chat_history:
        prompt += "\n\nPrevious Conversation Context:\n"
        for turn in chat_history:
            if hasattr(turn, 'user') and hasattr(turn, 'bot'):
                prompt += f"User: {turn.user}\nBot: {turn.bot}\n"
            elif isinstance(turn, dict):
                prompt += f"User: {turn['user']}\nBot: {turn['bot']}\n"
        
        prompt += "\nIMPORTANT: The user's current question is a follow-up to the previous conversation.\n"
        prompt += "When answering the current question:\n"
        prompt += "1. FIRST check the previous conversation context above for relevant information.\n"
        prompt += "2. If the follow-up question asks about details (like dates, locations, etc.), "
        prompt += "look for that information in the previous bot response.\n"
        prompt += "3. If the information is in the previous response, use it to answer the follow-up.\n"
        prompt += "4. If the information is not in the previous response but might be in the PMC records, "
        prompt += "search through the PMC records provided above.\n"
        prompt += "5. Only say information is not available if it's not in either the previous conversation OR the PMC records.\n"
    
    return prompt

def generate_response(prompt):
    """Generate response using OpenAI GPT"""
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

def remove_duplicate_links(text):
    """Remove duplicate links"""
    import re
    def url_replacer(match):
        url = match.group(2)  # Get the URL part
        if url in seen_urls:
            return ""
        seen_urls.add(url)
        return match.group(0)
    
    seen_urls = set()
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', url_replacer, text)

def main():
    """Main chat loop with improvements"""
    print(f"PMC Chatbot (Improved) - Using {LLM_MODEL} for generation and {EMBEDDING_MODEL} for search")
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
            
            # Enhanced sorting for latest queries
            if is_latest_query(user_input):
                def safe_date_sort(doc):
                    date_str = doc.metadata.get('date', doc.metadata.get('display_date', ''))
                    return parse_date_safe(date_str)
                docs = sorted(docs, key=safe_date_sort, reverse=True)
            
            # Use top N results for context
            context_docs = docs[:CONTEXT_RESULTS]
            pinecone_context = format_pinecone_results(context_docs) if context_docs else "No relevant information found."
            
            # Build prompt and generate response
            prompt = build_llm_prompt(user_input, pinecone_context, list(chat_history), lang)
            answer = generate_response(prompt)
            
            # Clean up the response
            answer = remove_duplicate_links(answer)
            
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