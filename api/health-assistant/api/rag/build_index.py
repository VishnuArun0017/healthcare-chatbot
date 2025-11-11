import chromadb
from pathlib import Path
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    
    return chunks


def build_index():
    """Build vector index from markdown files"""
    print("Building RAG index...")
    
    # Initialize Chroma client
    chroma_client = chromadb.PersistentClient(path="api/rag/chroma_db")
    
    # Create or get collection
    try:
        collection = chroma_client.delete_collection("medical_knowledge")
    except:
        pass
    
    collection = chroma_client.create_collection(
        name="medical_knowledge",
        metadata={"description": "Medical knowledge base"}
    )
    
    # Read all markdown files
    data_dir = Path("api/rag/data")
    documents = []
    metadatas = []
    ids = []
    
    for md_file in data_dir.glob("*.md"):
        print(f"Processing {md_file.name}...")
        
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Chunk the content
        chunks = chunk_text(content)
        
        for idx, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({
                "source": md_file.name,
                "chunk_id": idx
            })
            ids.append(f"{md_file.stem}#{idx}")
    
    # Add to collection
    print(f"Adding {len(documents)} chunks to index...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"✅ Index built successfully with {len(documents)} chunks from {len(list(data_dir.glob('*.md')))} files")


if __name__ == "__main__":
    build_index()