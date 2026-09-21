"""Similitud textual (TF-IDF + Jaccard) y detección de duplicados del analizador GIFT."""

import math
import re
from collections import Counter, defaultdict


class SimilitudMixin:
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for comparison."""
        text = text.lower()
        # Mantener letras, números y espacios
        text = re.sub(r'[^a-záéíóúñü0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _tokenize(self, text: str) -> list:
        """Tokenize text into words, keeping all tokens."""
        words = text.split()
        # Mantener todas las palabras/tokens, incluyendo números
        return [w for w in words if w]
    
    def _compute_word_freq(self, text: str) -> dict:
        """Compute word frequency."""
        words = self._tokenize(text)
        freq = defaultdict(int)
        for word in words:
            freq[word] += 1
        return dict(freq)
    
    def _compute_idf(self, all_texts: list) -> dict:
        """Compute IDF (inverse document frequency)."""
        doc_count = defaultdict(int)
        num_docs = len(all_texts)
        
        for text in all_texts:
            words = set(self._tokenize(text))
            for word in words:
                doc_count[word] += 1
        
        idf = {}
        for word, count in doc_count.items():
            idf[word] = math.log(num_docs / (1 + count))
        
        return idf
    
    def _compute_tfidf_vector(self, text: str, idf: dict) -> dict:
        """Compute TF-IDF vector."""
        freq = self._compute_word_freq(text)
        total_words = sum(freq.values())
        
        if total_words == 0:
            return {}
        
        tfidf = {}
        for word, count in freq.items():
            tf = count / total_words
            tfidf[word] = tf * idf.get(word, 0)
        
        return tfidf
    
    def _cosine_similarity(self, vec1: dict, vec2: dict) -> float:
        """Compute cosine similarity."""
        if not vec1 or not vec2:
            return 0.0
        
        # Unión de todas las palabras
        all_words = set(vec1.keys()) | set(vec2.keys())
        
        if not all_words:
            return 0.0
        
        # Calcular producto punto y magnitudes considerando todas las palabras
        dot_product = sum(vec1.get(word, 0) * vec2.get(word, 0) for word in all_words)
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two texts."""
        words1 = set(self._tokenize(text1))
        words2 = set(self._tokenize(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _combined_similarity(self, q1: dict, q2: dict) -> float:
        """Compute combined similarity using multiple metrics."""
        # Similitud de coseno TF-IDF
        cosine_sim = self._cosine_similarity(q1["vector"], q2["vector"])
        
        # Similitud Jaccard (más sensible a diferencias en palabras individuales)
        jaccard_sim = self._jaccard_similarity(q1["clean_text"], q2["clean_text"])
        
        # Combinar: promedio ponderado (Jaccard es más estricto)
        combined = (cosine_sim * 0.4) + (jaccard_sim * 0.6)
        
        return combined
    
    def find_duplicates(self):
        """Find duplicate or very similar questions."""
        self.duplicates = []
        if len(self.all_questions) < 2:
            return
        
        if self.verbose:
            print(f"Buscando duplicados con threshold {self.similarity_threshold}...")
        
        # Prepare texts
        for q in self.all_questions:
            q["clean_text"] = self._clean_text(q["full_text"])
        
        # Compute IDF
        all_texts = [q["clean_text"] for q in self.all_questions]
        idf = self._compute_idf(all_texts)
        
        # Compute TF-IDF vectors
        for q in self.all_questions:
            q["vector"] = self._compute_tfidf_vector(q["clean_text"], idf)
        
        # Compare questions
        for i in range(len(self.all_questions)):
            for j in range(i + 1, len(self.all_questions)):
                # Usar similitud combinada (TF-IDF coseno + Jaccard)
                similarity = self._combined_similarity(
                    self.all_questions[i],
                    self.all_questions[j]
                )
                
                if similarity >= self.similarity_threshold:
                    self.duplicates.append({
                        "index1": i,
                        "index2": j,
                        "similarity": similarity
                    })
        
        # Sort by similarity
        self.duplicates.sort(key=lambda x: x["similarity"], reverse=True)
