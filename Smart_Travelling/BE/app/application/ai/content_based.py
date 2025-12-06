import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os


@dataclass
class PlaceVector:
    """Vector biểu diễn của một địa điểm"""
    place_id: int
    place_name: str
    vector: np.ndarray
    tags: List[str]
    category: str


class ContentBasedRecommender:
    """Content-Based Filtering sử dụng TF-IDF và Cosine Similarity."""
    
    def __init__(self, model_path: str = "models/content_based"):
        self.model_path = model_path
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.place_vectors: Dict[int, PlaceVector] = {}
        self.place_matrix: Optional[np.ndarray] = None
        self.place_ids: List[int] = []
        
    def build_place_document(self, place) -> str:
        """Tạo document text từ thông tin địa điểm."""
        parts = []
        
        # Tags (trọng số cao nhất)
        tags = getattr(place, 'tags', None) or []
        if tags:
            if isinstance(tags, str):
                tags = [tags]
            tags_text = " ".join(tags)
            parts.extend([tags_text] * 3)
        
        # Category
        category = getattr(place, 'category', None) or ""
        if category:
            parts.extend([category] * 2)
        
        # Summary và Description
        summary = getattr(place, 'summary', None) or ""
        if summary:
            parts.append(summary)
        
        description = getattr(place, 'description', None) or ""
        if description:
            parts.append(description)
        
        # Name
        name = getattr(place, 'name', None) or ""
        if name:
            parts.append(name)
        
        return " ".join(parts).lower()
    
    def fit(self, places: List):
        """Train model với danh sách địa điểm."""
        if not places:
            raise ValueError("Không có địa điểm để train")
        
        documents = []
        self.place_ids = []
        
        for place in places:
            place_id = getattr(place, 'id', None) or getattr(place, 'place_id', None)
            if place_id is None:
                continue
                
            doc = self.build_place_document(place)
            if doc.strip():
                documents.append(doc)
                self.place_ids.append(place_id)
                
                tags = getattr(place, 'tags', None) or []
                if isinstance(tags, str):
                    tags = [tags]
                    
                self.place_vectors[place_id] = PlaceVector(
                    place_id=place_id,
                    place_name=getattr(place, 'name', '') or '',
                    vector=None,
                    tags=tags,
                    category=getattr(place, 'category', '') or ''
                )
        
        if not documents:
            raise ValueError("Không có document hợp lệ để train")
        
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            stop_words=self._get_vietnamese_stopwords()
        )
        
        self.place_matrix = self.vectorizer.fit_transform(documents).toarray()
        
        for idx, place_id in enumerate(self.place_ids):
            if place_id in self.place_vectors:
                self.place_vectors[place_id].vector = self.place_matrix[idx]
        
        print(f"✅ Content-Based: Trained on {len(self.place_ids)} places, vector dim: {self.place_matrix.shape[1]}")
    
    def build_user_profile(
        self,
        preferred_tags: List[str] = None,
        preferred_categories: List[str] = None,
        liked_place_ids: List[int] = None
    ) -> np.ndarray:
        """Tạo user profile vector từ preferences."""
        if self.vectorizer is None:
            raise ValueError("Model chưa được train")
        
        preferred_tags = preferred_tags or []
        preferred_categories = preferred_categories or []
        liked_place_ids = liked_place_ids or []
        
        user_doc_parts = []
        
        if preferred_tags:
            user_doc_parts.extend(preferred_tags * 3)
        
        if preferred_categories:
            user_doc_parts.extend(preferred_categories * 2)
        
        if liked_place_ids:
            liked_vectors = []
            for pid in liked_place_ids:
                if pid in self.place_vectors and self.place_vectors[pid].vector is not None:
                    liked_vectors.append(self.place_vectors[pid].vector)
            
            if liked_vectors:
                liked_avg = np.mean(liked_vectors, axis=0)
                
                if user_doc_parts:
                    user_doc = " ".join(user_doc_parts).lower()
                    pref_vector = self.vectorizer.transform([user_doc]).toarray()[0]
                    return 0.6 * liked_avg + 0.4 * pref_vector
                else:
                    return liked_avg
        
        if user_doc_parts:
            user_doc = " ".join(user_doc_parts).lower()
            return self.vectorizer.transform([user_doc]).toarray()[0]
        
        return np.zeros(self.place_matrix.shape[1])
    
    def recommend(
        self,
        user_profile: np.ndarray,
        top_k: int = 10,
        exclude_ids: List[int] = None,
        category_filter: str = None
    ) -> List[Tuple[int, float]]:
        """Recommend top_k địa điểm."""
        if self.place_matrix is None:
            return []
        
        exclude_ids = exclude_ids or []
        
        similarities = cosine_similarity([user_profile], self.place_matrix)[0]
        
        scored_places = []
        for idx, place_id in enumerate(self.place_ids):
            if place_id in exclude_ids:
                continue
            
            if category_filter:
                pv = self.place_vectors.get(place_id)
                if pv and pv.category.lower() != category_filter.lower():
                    continue
            
            scored_places.append((place_id, float(similarities[idx])))
        
        scored_places.sort(key=lambda x: x[1], reverse=True)
        return scored_places[:top_k]
    
    def get_similar_places(self, place_id: int, top_k: int = 5, exclude_ids: List[int] = None) -> List[Tuple[int, float]]:
        """Tìm địa điểm tương tự."""
        if place_id not in self.place_vectors:
            return []
        
        place_vector = self.place_vectors[place_id].vector
        if place_vector is None:
            return []
        
        exclude_ids = list(exclude_ids or [])
        exclude_ids.append(place_id)
        
        return self.recommend(place_vector, top_k, exclude_ids)
    
    def save_model(self):
        """Lưu model."""
        os.makedirs(self.model_path, exist_ok=True)
        
        with open(f"{self.model_path}/vectorizer.pkl", "wb") as f:
            pickle.dump(self.vectorizer, f)
        
        np.save(f"{self.model_path}/place_matrix.npy", self.place_matrix)
        
        with open(f"{self.model_path}/place_ids.pkl", "wb") as f:
            pickle.dump(self.place_ids, f)
        
        with open(f"{self.model_path}/place_vectors.pkl", "wb") as f:
            pickle.dump(self.place_vectors, f)
        
        print(f"✅ Content-Based model saved to {self.model_path}")
    
    def load_model(self) -> bool:
        """Load model."""
        try:
            with open(f"{self.model_path}/vectorizer.pkl", "rb") as f:
                self.vectorizer = pickle.load(f)
            
            self.place_matrix = np.load(f"{self.model_path}/place_matrix.npy")
            
            with open(f"{self.model_path}/place_ids.pkl", "rb") as f:
                self.place_ids = pickle.load(f)
            
            with open(f"{self.model_path}/place_vectors.pkl", "rb") as f:
                self.place_vectors = pickle.load(f)
            
            print(f"✅ Content-Based model loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            return False
    
    def _get_vietnamese_stopwords(self) -> List[str]:
        return [
            "và", "của", "là", "có", "được", "trong", "cho", "với",
            "này", "đó", "các", "một", "những", "từ", "để", "đến",
            "khi", "như", "về", "theo", "tại", "trên", "sau", "rất",
            "nhiều", "cũng", "còn", "nên", "bạn", "người", "nơi"
        ]