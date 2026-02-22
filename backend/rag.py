import os
import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# Load the sentence transformer model
model_name = "all-MiniLM-L6-v2"
embedder = SentenceTransformer(model_name)

class RAGPipeline:
    def __init__(self, docs_dir: str):
        self.docs_dir = docs_dir
        self.chunks = []      # List of dicts: {"text": str, "source": str, "page": int}
        self.index = None
        self.is_indexed = False

    def _extract_text_from_pdfs(self):
        """Extract text from all PDFs in the docs directory."""
        extracted_data = []
        if not os.path.exists(self.docs_dir):
            print(f"Warning: Directory {self.docs_dir} not found.")
            return extracted_data

        for filename in os.listdir(self.docs_dir):
            if filename.lower().endswith(".pdf"):
                filepath = os.path.join(self.docs_dir, filename)
                try:
                    reader = PdfReader(filepath)
                    for page_num, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text:
                            extracted_data.append({
                                "text": text,
                                "source": filename,
                                "page": page_num + 1
                            })
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        return extracted_data

    def _chunk_text(self, text_data, chunk_size=500, overlap=100):
        """Chunk text using a sliding window approach."""
        chunks = []
        for item in text_data:
            text = item["text"]
            source = item["source"]
            page = item["page"]
            
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end]
                chunks.append({
                    "text": chunk_text.strip(),
                    "source": source,
                    "page": page
                })
                start += (chunk_size - overlap)
        return chunks

    def build_index(self):
        """Extract, chunk, embed, and build the FAISS index."""
        print("Extracting text from PDFs...")
        text_data = self._extract_text_from_pdfs()
        
        if not text_data:
            print("No text data found. RAG index will be empty.")
            return

        print("Chunking text...")
        self.chunks = self._chunk_text(text_data)
        
        print(f"Generated {len(self.chunks)} chunks. Embedding...")
        texts = [chunk["text"] for chunk in self.chunks]
        
        embeddings = embedder.encode(texts, show_progress_bar=False)
        embeddings = np.array(embeddings).astype("float32")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        self.is_indexed = True
        print("FAISS index built successfully.")

    def retrieve(self, query: str, top_k: int = 3):
        """Retrieve top_k most relevant chunks for a give query."""
        if not self.is_indexed or self.index is None:
            return []

        # Embed query
        query_embedding = embedder.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")
        faiss.normalize_L2(query_embedding)

        # Search index
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunks) and idx >= 0:
                # Distances for IndexFlatIP are cosine similarities
                score = distances[0][i]
                chunk = self.chunks[idx]
                results.append({
                    "text": chunk["text"],
                    "document": chunk["source"],
                    "page": chunk["page"],
                    "relevance_score": float(score)
                })
        return results

# Singleton instance to be used by the API
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
docs_path = os.path.join(base_dir, "..", "clearpath_docs")
rag_pipeline = RAGPipeline(docs_dir=docs_path)
