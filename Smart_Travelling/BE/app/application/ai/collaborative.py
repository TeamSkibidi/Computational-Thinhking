import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
import pickle
import os


@dataclass
class UserInteraction:
    """Một tương tác của user với địa điểm"""
    user_id: int
    place_id: int
    rating: float
    timestamp: Optional[str] = None


class CollaborativeRecommender:
    """Collaborative Filtering sử dụng Matrix Factorization (SVD)."""
    
    def __init__(self, n_factors: int = 50, model_path: str = "models/collaborative"):
        self.n_factors = n_factors
        self.model_path = model_path
        
        self.svd: Optional[TruncatedSVD] = None
        self.user_factors: Optional[np.ndarray] = None
        self.item_factors: Optional[np.ndarray] = None
        
        self.user_id_map: Dict[int, int] = {}
        self.place_id_map: Dict[int, int] = {}
        self.reverse_place_map: Dict[int, int] = {}
        
        self.global_mean: float = 0.0
    
    def fit(self, interactions: List[UserInteraction]):
        """Train model từ danh sách tương tác."""
        if not interactions:
            raise ValueError("Không có dữ liệu tương tác")
        
        unique_users = sorted(set(i.user_id for i in interactions))
        unique_places = sorted(set(i.place_id for i in interactions))
        
        self.user_id_map = {uid: idx for idx, uid in enumerate(unique_users)}
        self.place_id_map = {pid: idx for idx, pid in enumerate(unique_places)}
        self.reverse_place_map = {idx: pid for pid, idx in self.place_id_map.items()}
        
        n_users = len(unique_users)
        n_places = len(unique_places)
        
        print(f"Building matrix: {n_users} users x {n_places} places")
        
        rows, cols, data = [], [], []
        for inter in interactions:
            rows.append(self.user_id_map[inter.user_id])
            cols.append(self.place_id_map[inter.place_id])
            data.append(inter.rating)
        
        interaction_matrix = csr_matrix((data, (rows, cols)), shape=(n_users, n_places))
        
        self.global_mean = np.mean(data)
        
        n_components = min(self.n_factors, min(n_users, n_places) - 1)
        if n_components < 1:
            n_components = 1
            
        self.svd = TruncatedSVD(n_components=n_components)
        self.user_factors = self.svd.fit_transform(interaction_matrix)
        self.item_factors = self.svd.components_.T
        
        print(f"✅ Collaborative: user_factors {self.user_factors.shape}, item_factors {self.item_factors.shape}")
    
    def recommend_for_user(self, user_id: int, top_k: int = 10, exclude_ids: List[int] = None) -> List[Tuple[int, float]]:
        """Recommend địa điểm cho user."""
        exclude_ids = exclude_ids or []
        
        if user_id not in self.user_id_map:
            return self._get_popular_items(top_k, exclude_ids)
        
        user_idx = self.user_id_map[user_id]
        user_vector = self.user_factors[user_idx]
        
        predicted_ratings = np.dot(user_vector, self.item_factors.T)
        
        scored_places = []
        for item_idx, score in enumerate(predicted_ratings):
            place_id = self.reverse_place_map[item_idx]
            if place_id not in exclude_ids:
                scored_places.append((place_id, float(score)))
        
        scored_places.sort(key=lambda x: x[1], reverse=True)
        return scored_places[:top_k]
    
    def _get_popular_items(self, top_k: int, exclude_ids: List[int]) -> List[Tuple[int, float]]:
        """Fallback cho cold start."""
        if self.item_factors is None:
            return []
            
        item_popularity = np.sum(np.abs(self.item_factors), axis=1)
        
        scored = []
        for idx, pop in enumerate(item_popularity):
            place_id = self.reverse_place_map[idx]
            if place_id not in exclude_ids:
                scored.append((place_id, float(pop)))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
    
    def save_model(self):
        """Lưu model."""
        os.makedirs(self.model_path, exist_ok=True)
        
        with open(f"{self.model_path}/svd.pkl", "wb") as f:
            pickle.dump(self.svd, f)
        
        np.save(f"{self.model_path}/user_factors.npy", self.user_factors)
        np.save(f"{self.model_path}/item_factors.npy", self.item_factors)
        
        with open(f"{self.model_path}/mappings.pkl", "wb") as f:
            pickle.dump({
                'user_id_map': self.user_id_map,
                'place_id_map': self.place_id_map,
                'reverse_place_map': self.reverse_place_map,
                'global_mean': self.global_mean
            }, f)
        
        print(f"✅ Collaborative model saved to {self.model_path}")
    
    def load_model(self) -> bool:
        """Load model."""
        try:
            with open(f"{self.model_path}/svd.pkl", "rb") as f:
                self.svd = pickle.load(f)
            
            self.user_factors = np.load(f"{self.model_path}/user_factors.npy")
            self.item_factors = np.load(f"{self.model_path}/item_factors.npy")
            
            with open(f"{self.model_path}/mappings.pkl", "rb") as f:
                mappings = pickle.load(f)
                self.user_id_map = mappings['user_id_map']
                self.place_id_map = mappings['place_id_map']
                self.reverse_place_map = mappings['reverse_place_map']
                self.global_mean = mappings['global_mean']
            
            print(f"✅ Collaborative model loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            return False