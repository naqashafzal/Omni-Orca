import os
import glob

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    import PyPDF2
    import docx
    PARSERS_AVAILABLE = True
except ImportError:
    PARSERS_AVAILABLE = False

# Persistent directory for document embeddings
INDEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_vault", "docs")

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    try:
        if ext in [".txt", ".md", ".csv", ".json", ".py", ".js", ".html"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        elif ext == ".pdf" and PARSERS_AVAILABLE:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        elif ext == ".docx" and PARSERS_AVAILABLE:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Failed to read {file_path}: {e}")
    return text

def chunk_text(text: str, chunk_size=1000, overlap=100) -> list:
    """Splits a large document into overlapping chunks of approx chunk_size characters."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_len = 0
    
    for word in words:
        current_chunk.append(word)
        current_len += len(word) + 1
        
        if current_len >= chunk_size:
            chunks.append(" ".join(current_chunk))
            # Keep the last 'overlap' words for context continuity
            overlap_words = current_chunk[-overlap:] if len(current_chunk) > overlap else []
            current_chunk = overlap_words
            current_len = sum(len(w) + 1 for w in current_chunk)
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

class DocumentIndexer:
    def __init__(self):
        if not CHROMA_AVAILABLE:
            self.collection = None
            print("⚠️ ChromaDB not installed. DocumentIndexer disabled.")
            return
            
        # Create persistent client inside the vault
        os.makedirs(INDEX_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=INDEX_DIR)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        
        # Collection purely for large document snippets
        self.collection = self.client.get_or_create_collection(
            name="local_documents", 
            embedding_function=self.ef
        )

    def index_folder(self, folder_path: str, max_files=100) -> str:
        """Deep scans a folder, extracts text from documents, chunks it, and vectorizes it."""
        if not self.collection:
            return "Error: ChromaDB offline."
            
        if not os.path.exists(folder_path):
            return f"Error: Folder '{folder_path}' does not exist."

        total_chunks = 0
        total_files = 0
        allowed_exts = {".txt", ".md", ".pdf", ".docx", ".csv", ".json"}
        
        # Walk directory
        for root, _, files in os.walk(folder_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in allowed_exts:
                    continue
                    
                total_files += 1
                if total_files > max_files:
                    break
                    
                full_path = os.path.join(root, file)
                # Ensure we haven't already indexed this file fully
                # A robust app would check hashes, but we'll do a simple metadata check
                existing = self.collection.get(where={"file": full_path}, limit=1)
                if existing and existing["ids"]:
                    continue # Skip already indexed
                
                text = extract_text(full_path)
                if not text.strip():
                    continue
                
                chunks = chunk_text(text)
                
                # Batch insert chunks
                if chunks:
                    ids = [f"{abs(hash(full_path))}_chunk_{i}" for i in range(len(chunks))]
                    metadatas = [{"file": full_path, "ext": ext} for _ in range(len(chunks))]
                    
                    self.collection.add(
                        documents=chunks,
                        metadatas=metadatas,
                        ids=ids
                    )
                    total_chunks += len(chunks)

        return f"Finished indexing. Scanned {total_files} files, generated {total_chunks} semantic text chunks."

    def search(self, query: str, n_results: int = 4) -> str:
        """Finds the most relevant document snippets based on the semantic query."""
        if not self.collection or self.collection.count() == 0:
            return "The Document Index is completely empty. Run 'index_folder' first."
            
        n = min(n_results, self.collection.count())
        results = self.collection.query(
            query_texts=[query],
            n_results=n
        )
        
        if not results or "documents" not in results or not results["documents"][0]:
            return "No relevant documents found."
            
        response_text = f"Top {n} matches from your local files for query: '{query}'\n\n"
        
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0]*len(docs)
        
        for i in range(len(docs)):
            score = round(1.0 - distances[i], 2) # Approximation of cosine sim from L2 squared
            file_name = os.path.basename(metas[i]["file"])
            snippet = docs[i].replace("\\n", " ").strip()[:500] + "..."
            response_text += f"---\nFILE: {file_name} (Relevance ~{score})\nPATH: {metas[i]['file']}\nSNIPPET: {snippet}\n"
            
        return response_text

if __name__ == "__main__":
    indexer = DocumentIndexer()
    print("Testing Universal RAG Engine...")
    test_dir = os.path.dirname(os.path.abspath(__file__))
    print(indexer.index_folder(test_dir, max_files=5))
    print(indexer.search("AI assistant architecture"))
