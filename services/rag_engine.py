"""
Medical RAG Engine
FAISS + sentence-transformers for offline medical knowledge retrieval
Documents are chunked (~300 tokens) for better retrieval accuracy.
Trusted sources (WHO / CDC / NICE / PubMed) are indexed and returned
with every query result so the LLM can cite them.
"""

import json
import os
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from utils.utils_logger import setup_logger

# Lazy import to avoid startup crash if faiss is not available
try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    logger = None  # Will be set after setup_logger below

logger = setup_logger(__name__)

# Lazy import to avoid slow startup
_model = None

# Chunking params
CHUNK_SIZE = 300  # ~300 tokens ≈ 900 chars
CHUNK_OVERLAP = 50  # overlap in tokens


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        model_path = "all-MiniLM-L6-v2"
        cache_dir = os.path.join(os.path.dirname(__file__), "..", "models", "embeddings")
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"Loading embedding model: {model_path}")
        _model = SentenceTransformer(model_path, cache_folder=cache_dir)
        logger.info("Embedding model loaded")
    return _model


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks of ~chunk_size tokens.
    Uses word-based splitting (1 token ~3 chars)."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def _format_sources_for_index(sources: List[Dict]) -> str:
    """
    Serialize trusted_sources into a plain-text string that gets embedded
    alongside the condition text, making sources searchable by FAISS.
    """
    if not sources:
        return ""
    parts = []
    for s in sources:
        pub = s.get("publisher", "")
        title = s.get("title", "")
        section = s.get("section", "")
        reviewed = s.get("last_reviewed", "")
        line = f"Source [{pub}]: {title}"
        if section:
            line += f" — {section}"
        if reviewed:
            line += f" (reviewed {reviewed})"
        parts.append(line)
    return "\n".join(parts)


class MedicalRAGEngine:
    """Offline RAG with FAISS vector search over medical knowledge base.
    Trusted sources (WHO/CDC/NICE/PubMed) are stored in the document
    metadata and surfaced in every context/citation response."""

    def __init__(self, knowledge_dir: str = "data/medical_knowledge"):
        self.knowledge_dir = knowledge_dir
        self.index = None
        self.documents: List[Dict] = []
        self.texts: List[str] = []
        self.index_path = os.path.join(knowledge_dir, "faiss_index.bin")
        self.docs_path = os.path.join(knowledge_dir, "indexed_docs.json")
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.docs_path):
                self._load_index()
            else:
                self._build_index()
            self._initialized = True
            logger.info(f"RAG Engine ready with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"RAG init error: {e}", exc_info=True)

    def _load_knowledge(self) -> List[Dict]:
        """
        Load all medical knowledge files, chunking long documents for
        better retrieval accuracy.

        UPDATED: trusted_sources are appended to the indexable text so
        FAISS can retrieve conditions via source-related queries, and the
        full source list is stored in every chunk's metadata for citation.
        """
        docs = []
        conditions_file = os.path.join(self.knowledge_dir, "conditions.json")
        if os.path.exists(conditions_file):
            with open(conditions_file, "r", encoding="utf-8") as f:
                conditions = json.load(f)
            for c in conditions:
                sources: List[Dict] = c.get("trusted_sources", [])
                sources_text = _format_sources_for_index(sources)

                text_parts = [
                    f"Condition: {c['name']}",
                    f"Category: {c.get('category', '')}",
                    f"Risk Level: {c.get('risk_level', '')}",
                    f"Symptoms: {', '.join(c.get('symptoms', []))}",
                    f"Causes: {', '.join(c.get('causes', []))}",
                    f"Home Remedies: {', '.join(c.get('home_remedies', []))}",
                    f"When to See Doctor: {', '.join(c.get('when_to_see_doctor', []))}",
                    f"Related Tests: {', '.join(c.get('related_tests', []))}",
                ]
                # Append source text so source names become searchable
                if sources_text:
                    text_parts.append(sources_text)

                full_text = "\n".join(text_parts)

                chunks = _chunk_text(full_text)
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{c['id']}_chunk{i}" if len(chunks) > 1 else c["id"]
                    docs.append({
                        "id": chunk_id,
                        "text": chunk,
                        "data": c,
                        "trusted_sources": sources,  # stored on every chunk
                    })

                # Also index individual symptom combinations for better matching
                if len(c.get("symptoms", [])) > 2:
                    symptom_text = (
                        f"Symptoms of {c['name']}: {', '.join(c['symptoms'])}. "
                        f"This condition is {c.get('risk_level', 'unknown')} risk."
                    )
                    if sources_text:
                        symptom_text += "\n" + sources_text
                    docs.append({
                        "id": f"{c['id']}_symptoms",
                        "text": symptom_text,
                        "data": c,
                        "trusted_sources": sources,
                    })

        return docs

    def _build_index(self):
        """Build FAISS index from medical knowledge"""
        if not HAS_FAISS:
            logger.warning("FAISS not available; RAG engine disabled")
            return
        
        raw_docs = self._load_knowledge()
        if not raw_docs:
            logger.warning("No medical knowledge documents found")
            return

        model = _get_model()
        self.documents = raw_docs
        self.texts = [d["text"] for d in raw_docs]

        logger.info(f"Encoding {len(self.texts)} documents...")
        embeddings = model.encode(self.texts, show_progress_bar=False, normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype=np.float32)

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

        faiss.write_index(self.index, self.index_path)
        with open(self.docs_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False)
        logger.info(f"FAISS index built and saved: {len(self.texts)} docs, dim={dim}")

    def _load_index(self):
        """Load pre-built FAISS index"""
        if not HAS_FAISS:
            logger.warning("FAISS not available; RAG engine disabled")
            return
        
        self.index = faiss.read_index(self.index_path)
        with open(self.docs_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)
        self.texts = [d["text"] for d in self.documents]
        logger.info(f"FAISS index loaded: {len(self.texts)} docs")

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search medical knowledge for relevant documents.
        Returns documents including their trusted_sources metadata."""
        if not self._initialized or self.index is None:
            return []

        model = _get_model()
        query_vec = model.encode([query], normalize_embeddings=True)
        query_vec = np.array(query_vec, dtype=np.float32)

        scores, indices = self.index.search(query_vec, min(top_k, len(self.texts)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            doc = self.documents[idx]
            results.append({
                "score": float(score),
                "id": doc["id"],
                "text": doc["text"],
                "data": doc.get("data", {}),
                "trusted_sources": doc.get("trusted_sources", []),
            })
        return results

    def get_context_for_query(self, query: str, top_k: int = 3) -> str:
        """
        Get formatted medical context for LLM prompt.

        UPDATED: Appends a 'Trusted Sources' block so the LLM can
        naturally reference/cite them in its response.
        """
        results = self.search(query, top_k)
        if not results:
            return ""

        parts = ["Medical Reference Information:"]
        seen_conditions = set()
        all_sources: List[Dict] = []
        seen_source_urls: set = set()

        for r in results:
            cond_data = r.get("data", {})
            cond_id = cond_data.get("id", r["id"])
            if cond_id in seen_conditions:
                continue
            seen_conditions.add(cond_id)

            name     = cond_data.get("name", "")
            risk     = cond_data.get("risk_level", "")
            symptoms = cond_data.get("symptoms", [])
            causes   = cond_data.get("causes", [])
            remedies = cond_data.get("home_remedies", [])
            when_doc = cond_data.get("when_to_see_doctor", [])
            tests    = cond_data.get("related_tests", [])

            parts.append(f"\n--- {name} (Risk: {risk}) ---")
            if symptoms:
                parts.append(f"Symptoms: {', '.join(symptoms[:8])}")
            if causes:
                parts.append(f"Possible Causes: {', '.join(causes[:5])}")
            if remedies:
                parts.append(f"Home Remedies: {', '.join(remedies[:5])}")
            if when_doc:
                parts.append(f"See Doctor If: {', '.join(when_doc[:4])}")
            if tests:
                parts.append(f"Recommended Tests: {', '.join(tests[:4])}")

            # Collect de-duplicated sources
            for src in r.get("trusted_sources", []):
                url = src.get("url", "")
                if url and url not in seen_source_urls:
                    seen_source_urls.add(url)
                    all_sources.append(src)

        # Append trusted-source citation block
        if all_sources:
            parts.append("\n--- Trusted Medical Sources ---")
            for src in all_sources:
                pub      = src.get("publisher", "")
                title    = src.get("title", "")
                url      = src.get("url", "")
                section  = src.get("section", "")
                reviewed = src.get("last_reviewed", "")
                line = f"[{pub}] {title}"
                if section:
                    line += f" — {section}"
                if reviewed:
                    line += f" (last reviewed {reviewed})"
                if url:
                    line += f"\n  URL: {url}"
                parts.append(line)

        return "\n".join(parts)

    def get_citations_for_query(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Return a clean, deduplicated list of citation objects for the
        top-k conditions matched by the query.  Used by API endpoints
        to attach citations directly to JSON responses.

        Each item:
            {
                "condition":     "Migraine",
                "publisher":     "WHO",
                "title":         "Headache Disorders Fact Sheet",
                "url":           "https://...",
                "section":       "Migraine",
                "last_reviewed": "2023-04"
            }
        """
        results = self.search(query, top_k)
        citations: List[Dict] = []
        seen_urls: set = set()
        seen_conditions: set = set()

        for r in results:
            cond_data = r.get("data", {})
            cond_id   = cond_data.get("id", r["id"])
            cond_name = cond_data.get("name", cond_id)

            if cond_id in seen_conditions:
                continue
            seen_conditions.add(cond_id)

            for src in r.get("trusted_sources", []):
                url = src.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    citations.append({
                        "condition":     cond_name,
                        "publisher":     src.get("publisher", ""),
                        "title":         src.get("title", ""),
                        "url":           url,
                        "section":       src.get("section", ""),
                        "last_reviewed": src.get("last_reviewed", ""),
                    })

        return citations

    def rebuild_index(self):
        """Force rebuild of the FAISS index (call after updating conditions.json)."""
        self._initialized = False
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.docs_path):
            os.remove(self.docs_path)
        self._build_index()
        self._initialized = True

    def check_health(self) -> bool:
        return self._initialized and self.index is not None