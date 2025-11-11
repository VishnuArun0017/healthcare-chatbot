import chromadb
from chromadb.config import Settings
from pathlib import Path
import os
import sys
import re
import yaml

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from markdown file"""
    frontmatter = {}
    body = content
    
    # Check for YAML frontmatter (--- markers)
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
            except yaml.YAMLError:
                # If YAML parsing fails, treat entire content as body
                pass
    
    return frontmatter, body


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
    """Build vector index from markdown files (recursively scans subdirectories)"""
    print("Building RAG index...")
    
    # Get the correct path
    script_dir = Path(__file__).parent
    chroma_path = script_dir / "chroma_db"
    data_dir = script_dir / "data"
    
    print(f"Data directory: {data_dir}")
    print(f"Chroma path: {chroma_path}")
    
    # Initialize Chroma client
    chroma_client = chromadb.PersistentClient(
        path=str(chroma_path),
        settings=Settings(anonymized_telemetry=False),
    )
    
    # Create or get collection
    try:
        collection = chroma_client.delete_collection("medical_knowledge")
        print("Deleted existing collection")
    except:
        pass
    
    collection = chroma_client.create_collection(
        name="medical_knowledge",
        metadata={"description": "Medical knowledge base"}
    )
    
    # Read all markdown files recursively
    documents = []
    metadatas = []
    ids = []
    
    md_files = list(data_dir.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files")
    
    for md_file in md_files:
        # Get relative path for topic/category
        relative_path = md_file.relative_to(data_dir)
        category = relative_path.parent.name if relative_path.parent != Path(".") else "general"
        
        print(f"Processing {relative_path}...")
        
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract frontmatter if present
        frontmatter, body = extract_frontmatter(content)
        
        # Extract metadata
        title = frontmatter.get("title", md_file.stem.replace("_", " ").replace("-", " "))
        topic = frontmatter.get("id", md_file.stem)
        sources = frontmatter.get("sources", [])
        
        # Chunk the content
        chunks = chunk_text(body)
        
        for idx, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append(
                {
                    "source": str(relative_path),
                    "source_file": md_file.name,
                    "category": category,
                    "title": title,
                    "topic": topic,
                    "chunk_id": idx,
                }
            )
            # Use POSIX relative path (without extension) to guarantee unique IDs across folders
            relative_id = relative_path.with_suffix("").as_posix()
            ids.append(f"{relative_id}#{idx}")
    
    # Add to collection
    print(f"Adding {len(documents)} chunks to index...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Index built successfully with {len(documents)} chunks from {len(md_files)} files")


if __name__ == "__main__":
    build_index()