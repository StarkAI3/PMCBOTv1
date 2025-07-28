import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_INDEX = os.getenv('PINECONE_INDEX', 'pmc-chatbot-index')

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

def clear_index():
    """Clear all vectors from the Pinecone index"""
    try:
        # Get the index
        index = pc.Index(PINECONE_INDEX)
        
        # Get index stats to see current data
        stats = index.describe_index_stats()
        total_vectors = stats.get('total_vector_count', 0)
        
        print(f"Current index '{PINECONE_INDEX}' has {total_vectors} vectors")
        
        if total_vectors == 0:
            print("Index is already empty!")
            return
        
        # Confirm deletion
        response = input(f"Are you sure you want to delete all {total_vectors} vectors? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("Operation cancelled.")
            return
        
        print("Deleting all vectors...")
        
        # Delete all vectors using delete_all parameter
        print("Deleting all vectors...")
        index.delete(delete_all=True)
        
        # Verify deletion
        new_stats = index.describe_index_stats()
        new_total = new_stats.get('total_vector_count', 0)
        
        print(f"✅ Successfully cleared index!")
        print(f"Remaining vectors: {new_total}")
        
        # Also delete progress file if it exists
        progress_file = 'embedding_progress.json'
        if os.path.exists(progress_file):
            os.remove(progress_file)
            print(f"✅ Deleted progress file: {progress_file}")
        
    except Exception as e:
        print(f"❌ Error clearing index: {e}")

def main():
    print("Pinecone Index Clear Tool")
    print("=" * 30)
    print(f"Index: {PINECONE_INDEX}")
    print()
    
    clear_index()

if __name__ == '__main__':
    main() 