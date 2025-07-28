import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENV = os.getenv('PINECONE_ENV')

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

def create_optimized_index():
    """Create an optimized Pinecone index for PMC chatbot"""
    
    # Index configuration
    index_name = "pmc-chatbot-index"
    
    # Choose embedding model and dimensions
    print("Choose your embedding model:")
    print("1. text-embedding-3-small (1536 dimensions) - Recommended for cost-performance balance")
    print("2. text-embedding-3-large (3072 dimensions) - Best accuracy, higher cost")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "2":
        dimensions = 3072
        embedding_model = "text-embedding-3-large"
    else:
        dimensions = 1536
        embedding_model = "text-embedding-3-small"
    
    print(f"\nCreating index with {embedding_model} ({dimensions} dimensions)...")
    
    # Check if index already exists
    existing_indexes = pc.list_indexes()
    if index_name in [idx.name for idx in existing_indexes]:
        print(f"Index '{index_name}' already exists!")
        response = input("Do you want to delete and recreate it? (y/n): ").strip().lower()
        if response == 'y':
            print(f"Deleting existing index '{index_name}'...")
            pc.delete_index(index_name)
        else:
            print("Operation cancelled.")
            return
    
    # Create index with optimal configuration
    try:
        pc.create_index(
            name=index_name,
            dimension=dimensions,
            metric="cosine",  # Best for semantic search
            spec={
                "serverless": {
                    "cloud": "aws",
                    "region": "us-east-1"
                }
            }
        )
        
        print(f"\n✅ Successfully created Pinecone index: {index_name}")
        print(f"📊 Configuration:")
        print(f"   - Dimensions: {dimensions}")
        print(f"   - Metric: cosine")
        print(f"   - Type: Serverless")
        print(f"   - Cloud: AWS")
        print(f"   - Region: us-east-1")
        print(f"   - Embedding Model: {embedding_model}")
        
        print(f"\n🔧 Next steps:")
        print(f"1. Update your .env file with:")
        print(f"   PINECONE_INDEX={index_name}")
        print(f"2. Run the embedding script:")
        print(f"   python scripts/embed_and_upsert_openai.py")
        print(f"3. Test the chatbot:")
        print(f"   python chatbot/terminal_chatbot_openai.py")
        
    except Exception as e:
        print(f"❌ Error creating index: {e}")

def list_existing_indexes():
    """List all existing indexes"""
    print("Existing Pinecone indexes:")
    indexes = pc.list_indexes()
    if not indexes:
        print("No indexes found.")
    else:
        for idx in indexes:
            print(f"  - {idx.name} (dimensions: {idx.dimension})")

def main():
    print("Pinecone Index Management for PMC Chatbot")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Create optimized index")
        print("2. List existing indexes")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            create_optimized_index()
        elif choice == "2":
            list_existing_indexes()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main() 