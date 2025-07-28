import os
import json
from tqdm import tqdm
from dotenv import load_dotenv
from pinecone import Pinecone
import openai
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENV = os.getenv('PINECONE_ENV')
PINECONE_INDEX = os.getenv('PINECONE_INDEX', 'pmc-bot-index')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# File path
DATA_FILE = 'data/pmc_data_normalized.jsonl'
BATCH_SIZE = 10  # Reduced to avoid Pinecone API limits
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200
PROGRESS_FILE = 'embedding_progress.json'  # Track progress

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# Initialize OpenAI
if not OPENAI_API_KEY:
    raise ValueError('OPENAI_API_KEY not set in .env')
openai.api_key = OPENAI_API_KEY

# Use text-embedding-3-small for cost-performance balance
# Switch to text-embedding-3-large for maximum accuracy
EMBEDDING_MODEL = 'text-embedding-3-small'

def embed_text(text):
    """OpenAI embedding API with error handling and retries"""
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
        print(f'Embedding error: {e}')
        return None

def chunk_text(text):
    """Intelligent text chunking for better semantic coherence"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
    )
    return splitter.split_text(text)

def filter_metadata(meta):
    """Filter metadata to only include essential fields within Pinecone limits"""
    # Only keep essential metadata fields to stay within 40KB limit
    essential_fields = {
        'id', 'title', 'description', 'date', 'display_date', 
        'department', 'ward_name', 'record_type', 'lang',
        'pdf_url', 'external_link', 'url', 'chunk_id', 'total_chunks',
        'embedding_model'
    }
    
    filtered = {}
    for k, v in meta.items():
        if k in essential_fields:
            if isinstance(v, str) and len(v) > 1000:  # Truncate long strings
                filtered[k] = v[:1000] + "..."
            elif isinstance(v, (str, int, float, bool)):
                filtered[k] = v
            elif isinstance(v, list) and all(isinstance(i, str) for i in v):
                # Truncate list items if too long
                filtered[k] = [item[:500] + "..." if len(item) > 500 else item for item in v[:5]]
    
    return filtered

def extract_text_for_embedding(rec):
    """Enhanced text extraction optimized for OpenAI embeddings"""
    text_parts = []
    
    # Use the enhanced full_content if available
    if rec.get('full_content'):
        text_parts.append(rec['full_content'])
    else:
        # Fallback to original method with improvements
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
    
    # Add contact information if available
    contact = rec.get('contact')
    if contact:
        text_parts.append(f"Contact: {contact}")
    
    return "\n".join(text_parts)

def load_progress():
    """Load progress from file"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'processed_records': set(), 'total_embeddings': 0}

def save_progress(progress):
    """Save progress to file"""
    # Convert set to list for JSON serialization
    progress['processed_records'] = list(progress['processed_records'])
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def main():
    """Main function to embed and upsert PMC data"""
    # Load progress
    progress = load_progress()
    processed_records = set(progress['processed_records'])
    
    records = []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            rec = json.loads(line)
            records.append(rec)
    
    # Filter out already processed records
    unprocessed_records = [rec for rec in records if rec['id'] not in processed_records]
    
    print(f'Total records: {len(records)}')
    print(f'Already processed: {len(processed_records)}')
    print(f'Remaining to process: {len(unprocessed_records)}')
    
    if len(unprocessed_records) == 0:
        print('All records already processed!')
        return
    
    # Print statistics for unprocessed records
    type_counts = {}
    lang_counts = {}
    for rec in unprocessed_records:
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
    
    print(f'\nUsing OpenAI embedding model: {EMBEDDING_MODEL}')
    
    batch = []
    total_embeddings = progress['total_embeddings']
    
    for rec in tqdm(unprocessed_records, desc='Embedding and upserting'):
        # Use enhanced text extraction
        text = extract_text_for_embedding(rec)
        
        # Skip if no meaningful text
        if not text or len(text.strip()) < 10:
            continue
        
        # Chunk if too large (OpenAI has 8192 token limit)
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
                meta['embedding_model'] = EMBEDDING_MODEL
                # Don't include full text in metadata to stay within limits
                meta = filter_metadata(meta)
                batch.append({'id': chunk_id, 'values': embedding, 'metadata': meta})
                total_embeddings += 1
            
            if len(batch) >= BATCH_SIZE:
                try:
                    index.upsert(vectors=batch)
                    print(f"Successfully upserted batch of {len(batch)} vectors")
                    # Mark record as processed
                    processed_records.add(rec['id'])
                    # Save progress periodically
                    progress['processed_records'] = processed_records
                    progress['total_embeddings'] = total_embeddings
                    save_progress(progress)
                except Exception as e:
                    print(f"Error upserting batch: {e}")
                    # Try upserting one by one if batch fails
                    for vector in batch:
                        try:
                            index.upsert(vectors=[vector])
                        except Exception as e2:
                            print(f"Error upserting individual vector {vector['id']}: {e2}")
                    # Mark record as processed even if some chunks failed
                    processed_records.add(rec['id'])
                    progress['processed_records'] = processed_records
                    progress['total_embeddings'] = total_embeddings
                    save_progress(progress)
                batch = []
    
    if batch:
        try:
            index.upsert(vectors=batch)
            print(f"Successfully upserted final batch of {len(batch)} vectors")
        except Exception as e:
            print(f"Error upserting final batch: {e}")
            # Try upserting one by one if batch fails
            for vector in batch:
                try:
                    index.upsert(vectors=[vector])
                except Exception as e2:
                    print(f"Error upserting individual vector {vector['id']}: {e2}")
    
    # Final progress save
    progress['processed_records'] = processed_records
    progress['total_embeddings'] = total_embeddings
    save_progress(progress)
    
    print(f'\nEmbedding and upsert complete.')
    print(f'Total embeddings created: {total_embeddings}')
    print(f'Records processed: {len(processed_records)}')
    print(f'Index: {PINECONE_INDEX}')
    print(f'Model: {EMBEDDING_MODEL}')
    print(f'Progress saved to: {PROGRESS_FILE}')

if __name__ == '__main__':
    main() 