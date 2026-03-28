import os

# We will conditionally import chromadb so the rest of the app doesn't crash if it's missing
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

# Define the persistent directory for memory
MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_vault")

class MemoryAgent:
    def __init__(self):
        if not CHROMA_AVAILABLE:
            self.collection = None
            print("⚠️ ChromaDB not found. MemoryAgent is disabled. Run: pip install chromadb")
            return
            
        # Create persistent client
        self.client = chromadb.PersistentClient(path=MEMORY_DIR)
        
        # We will use the default SentenceTransformer embedding function
        # It downloads a tiny ~90MB model on first run, cached locally.
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create the 'user_facts' collection
        self.collection = self.client.get_or_create_collection(
            name="user_facts", 
            embedding_function=self.ef
        )
        
    def memorize(self, fact: str, source: str = "Command Center") -> str:
        """Stores a new fact about the user or system into long-term memory."""
        if not self.collection:
            return "Memory Engine is offline."
            
        # We use a simple hash of the fact as the ID to avoid exact duplicates
        fact_id = f"fact_{abs(hash(fact))}"
        
        # Check if already exists exactly
        existing = self.collection.get(ids=[fact_id])
        if existing and existing["ids"]:
            return f"Fact already known: '{fact}'"
            
        self.collection.add(
            documents=[fact],
            metadatas=[{"source": source}],
            ids=[fact_id]
        )
        return f"Successfully committed to LTM: '{fact}'"
        
    def recall(self, query: str, n_results: int = 3) -> list:
        """Retrieves facts relevant to the query from long-term memory."""
        if not self.collection:
            return []
            
        # If DB is empty, return nothing
        if self.collection.count() == 0:
            return []
            
        # Ensure n_results doesn't exceed total facts
        n = min(n_results, self.collection.count())
        if n == 0:
            return []
            
        results = self.collection.query(
            query_texts=[query],
            n_results=n
        )
        
        # Results structure: {'documents': [['fact1', 'fact2']], ...}
        if results and "documents" in results and results["documents"]:
            return results["documents"][0]
        return []

    def get_all_facts(self) -> list:
        """Returns all facts stored in the database (for GUI display/debugging)."""
        if not self.collection or self.collection.count() == 0:
            return []
            
        results = self.collection.get()
        if results and "documents" in results:
            return results["documents"]
        return []

    def forget_fact(self, fact_text: str) -> bool:
        """Deletes a specific fact from memory."""
        if not self.collection:
            return False
            
        results = self.collection.get()
        if not results or "documents" not in results:
            return False
            
        for doc_id, doc in zip(results["ids"], results["documents"]):
            if doc == fact_text:
                self.collection.delete(ids=[doc_id])
                return True
        return False
        
# For standalone testing
if __name__ == "__main__":
    mem = MemoryAgent()
    if CHROMA_AVAILABLE:
        print("Testing Memory Storage...")
        mem.memorize("The user works as a Software Engineer at Zakria Sons.", "Test")
        mem.memorize("The user prefers precise, concise Python code.", "Test")
        
        print("\nRecalling memory for query 'What is my job?':")
        recalled = mem.recall("What is my job?")
        for item in recalled:
            print("  ->", item)
