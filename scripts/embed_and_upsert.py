import os
import json
from tqdm import tqdm
from dotenv import load_dotenv
from pinecone import Pinecone
import google.generativeai as genai
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENV = os.getenv('PINECONE_ENV')
PINECONE_INDEX = os.getenv('PINECONE_INDEX', 'pmc-bot-index')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# File path
DATA_FILE = 'data/pmc_data_normalized.jsonl'
BATCH_SIZE = 50
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# Initialize Gemini
if not GEMINI_API_KEY:
    raise ValueError('GEMINI_API_KEY not set in .env')
genai.configure(api_key=GEMINI_API_KEY)
embed_model = genai.embed_content

def embed_text(text):
    # Gemini embedding API
    try:
        response = embed_model(model='models/embedding-001', content=text, task_type='retrieval_document')
        return response['embedding']
    except Exception as e:
        print(f'Embedding error: {e}')
        return None

def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_text(text)

def filter_metadata(meta):
    # Only keep primitive types or list of strings
    allowed_types = (str, int, float, bool)
    filtered = {}
    for k, v in meta.items():
        if k == 'raw':
            continue
        if isinstance(v, allowed_types):
            filtered[k] = v
        elif isinstance(v, list) and all(isinstance(i, str) for i in v):
            filtered[k] = v
    return filtered

def extract_text_for_embedding(rec):
    """Enhanced text extraction for better semantic search."""
    text_parts = []
    
    # Use the enhanced full_content if available
    if rec.get('full_content'):
        text_parts.append(rec['full_content'])
    else:
        # Fallback to original method
        title = rec.get('title', '')
        if title:
            text_parts.append(f"Title: {title}")
        
        description = rec.get('description')
        if description:
            text_parts.append(f"Description: {description}")
        
        # Add other important fields
        long_desc = rec.get('long_description')
        if long_desc:
            text_parts.append(f"Details: {long_desc}")
        
        summary = rec.get('summary')
        if summary:
            if isinstance(summary, list):
                for item in summary:
                    text_parts.append(f"Summary: {item}")
            else:
                text_parts.append(f"Summary: {summary}")
    
    # Add department and ward information for better context
    department = rec.get('department')
    if department:
        text_parts.append(f"Department: {department}")
    
    ward_name = rec.get('ward_name')
    if ward_name:
        text_parts.append(f"Ward: {ward_name}")
    
    # Add record type for better categorization
    record_type = rec.get('record_type')
    if record_type and record_type != 'other':
        text_parts.append(f"Type: {record_type}")
    
    return "\n".join(text_parts)

def main():
    records = []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            rec = json.loads(line)
            records.append(rec)
    print(f'Total records to embed: {len(records)}')
    
    # Print some statistics
    type_counts = {}
    lang_counts = {}
    for rec in records:
        rec_type = rec.get('record_type', 'unknown')
        type_counts[rec_type] = type_counts.get(rec_type, 0) + 1
        lang = rec.get('lang', 'unknown')
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    
    print(f'\nRecord type distribution:')
    for rec_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f'  {rec_type}: {count}')
    
    print(f'\nLanguage distribution:')
    for lang, count in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True):
        print(f'  {lang}: {count}')
    
    batch = []
    for rec in tqdm(records, desc='Embedding and upserting'):
        # Use enhanced text extraction
        text = extract_text_for_embedding(rec)
        
        # Skip if no meaningful text
        if not text or len(text.strip()) < 10:
            continue
        
        # Chunk if too large
        if len(text) > 30000:
            chunks = chunk_text(text)
        else:
            chunks = [text]
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{rec['id']}_chunk{i+1}" if len(chunks) > 1 else rec['id']
            embedding = embed_text(chunk)
            if embedding:
                meta = rec.copy()
                meta['chunk_id'] = i+1
                meta['total_chunks'] = len(chunks)
                meta['text'] = chunk
                meta = filter_metadata(meta)
                batch.append({'id': chunk_id, 'values': embedding, 'metadata': meta})
            
            if len(batch) >= BATCH_SIZE:
                index.upsert(vectors=batch)
                batch = []
    
    if batch:
        index.upsert(vectors=batch)
    
    print('Embedding and upsert complete.')

if __name__ == '__main__':
    main() 