"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import glob
import re

class DocuBot:
    # Palabras comunes en inglés que no aportan significado a la búsqueda
    STOPWORDS = {
        "a", "an", "the", "is", "are", "was", "were", "to", "of", "in", "for", 
        "on", "with", "at", "by", "from", "up", "about", "into", "over", "after", 
        "how", "do", "i", "you", "we", "they", "he", "she", "it", "can", "my", 
        "your", "this", "that", "and", "or", "but", "where", "what", "when"
    }

    def __init__(self, docs_folder="docs", llm_client=None):
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        # Load documents into memory
        self.documents = self.load_documents()

        # Build a retrieval index
        self.index = self.build_index(self.documents)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                docs.append((filename, text))
        return docs

    # -----------------------------------------------------------
    # Index Construction
    # -----------------------------------------------------------

    def build_index(self, documents):
        index = {}
        for filename, text in documents:
            words = re.findall(r'\b\w+\b', text.lower())
            for word in words:
                if word not in index:
                    index[word] = []
                if filename not in index[word]:
                    index[word].append(filename)
        return index

    # -----------------------------------------------------------
    # Scoring and Retrieval
    # -----------------------------------------------------------

    def score_document(self, query, text):
        """
        Calcula el score, pero ignorando las stopwords.
        """
        query_words = re.findall(r'\b\w+\b', query.lower())
        # Filtramos las stopwords de la pregunta
        meaningful_words = [w for w in query_words if w not in self.STOPWORDS]
        
        text_lower = text.lower()
        score = 0
        
        # Solo sumamos puntos por palabras importantes
        for word in meaningful_words:
            score += text_lower.count(word)
            
        return score

    def retrieve(self, query, top_k=3, min_score=1):
        """
        Busca fragmentos relevantes con guardrail.
        """
        scored_chunks = []
        
        query_words = re.findall(r'\b\w+\b', query.lower())
        meaningful_words = [w for w in query_words if w not in self.STOPWORDS]
        
        # Si la pregunta no tiene palabras clave, no hay nada que buscar
        if not meaningful_words:
            return []

        # Filtramos los documentos candidatos
        candidate_filenames = set()
        for word in meaningful_words:
            if word in self.index:
                candidate_filenames.update(self.index[word])
                
        # Calculamos el score por fragmentos
        for filename, text in self.documents:
            if filename in candidate_filenames:
                chunks = text.split("\n")
                for chunk in chunks:
                    chunk = chunk.strip()
                    if not chunk:
                        continue
                    
                    score = self.score_document(query, chunk)
                    
                    # GUARDRAIL: Solo lo añadimos si el score es mayor o igual al mínimo
                    if score >= min_score:
                        scored_chunks.append((filename, chunk, score))
        
        # Ordenamos de mayor a menor score
        scored_chunks.sort(key=lambda x: x[2], reverse=True)
        
        results = [(filename, chunk) for filename, chunk, score in scored_chunks]
        
        return results[:top_k]

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=3):
        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        formatted = []
        for filename, text in snippets:
            formatted.append(f"[{filename}]\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        return self.llm_client.answer_from_snippets(query, snippets)

    # -----------------------------------------------------------
    # Bonus Helper
    # -----------------------------------------------------------

    def full_corpus_text(self):
        return "\n\n".join(text for _, text in self.documents)