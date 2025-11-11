import chromadb
from typing import List, Dict


def retrieve(query: str, k: int = 4) -> List[Dict[str, str]]:
    """
    Retrieve relevant chunks from the vector database
    
    Args:
        query: Search query
        k: Number of results to return
        
    Returns:
        List of dictionaries with 'chunk' and 'id' keys
    """
    try:
        # Initialize Chroma client
        chroma_client = chromadb.PersistentClient(path="api/rag/chroma_db")
        
        # Get collection
        collection = chroma_client.get_collection("medical_knowledge")
        
        # Query the collection
        results = collection.query(
            query_texts=[query],
            n_results=k
        )
        
        # Format results
        retrieved = []
        if results["documents"] and results["documents"][0]:
            for chunk, chunk_id, metadata in zip(
                results["documents"][0],
                results["ids"][0],
                results["metadatas"][0]
            ):
                retrieved.append({
                    "chunk": chunk,
                    "id": chunk_id,
                    "source": metadata.get("source", "unknown")
                })
        
        return retrieved
    
    except Exception as e:
        print(f"Retrieval error: {e}")
        return []


def test_retrieval():
    """Test the retrieval function"""
    test_queries = [
        "I have fever and body ache",
        "What should I do for sore throat?",
        "Chest pain and shortness of breath"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = retrieve(query, k=2)
        for r in results:
            print(f"  📄 {r['source']}: {r['chunk'][:100]}...")


if __name__ == "__main__":
    test_retrieval()