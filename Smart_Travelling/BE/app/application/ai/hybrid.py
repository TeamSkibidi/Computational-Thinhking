from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from app.domain.entities.place_lite import PlaceLite

from .content_based import ContentBasedRecommender
from .collaborative import CollaborativeRecommender, UserInteraction


@dataclass
class HybridConfig:
    """Cấu hình trọng số cho hybrid model"""
    content_weight: float = 0.5
    collaborative_weight: float = 0.3
    popularity_weight: float = 0.2


class HybridRecommender:
    """Hybrid Recommendation System kết hợp Content-Based + Collaborative + Popularity."""
    
    def __init__(self, config: HybridConfig = None):
        self.config = config or HybridConfig()
        self.content_model = ContentBasedRecommender()
        self.collab_model = CollaborativeRecommender()
        
        self.places_by_id: Dict[int, any] = {}
        self.is_trained = False
    
    def fit(self, places: List[PlaceLite], interactions: List[UserInteraction] = None):
        """Train cả hai models."""
        # Index places
        for p in places:
            place_id = getattr(p, 'id', None) or getattr(p, 'place_id', None)
            if place_id:
                self.places_by_id[place_id] = p
        
        # Train content-based
        print("Training Content-Based model...")
        self.content_model.fit(places)
        
        # Train collaborative nếu có data
        if interactions and len(interactions) > 0:
            print("Training Collaborative model...")
            self.collab_model.fit(interactions)
        
        self.is_trained = True
        print("Hybrid model trained successfully!")
    
    def recommend(
        self,
        user_id: Optional[int] = None,
        preferred_tags: List[str] = None,
        preferred_categories: List[str] = None,
        liked_place_ids: List[int] = None,
        exclude_ids: List[int] = None,
        top_k: int = 10,
        category_filter: str = None
    ) -> List[Tuple[any, float, Dict[str, float]]]:
        """Recommend địa điểm kết hợp cả 3 nguồn."""
        if not self.is_trained:
            raise ValueError("Model chưa được train")
        
        exclude_ids = exclude_ids or []
        preferred_tags = preferred_tags or []
        
        # 1. Content-Based scores
        content_scores = {}
        if preferred_tags or preferred_categories or liked_place_ids:
            user_profile = self.content_model.build_user_profile(
                preferred_tags=preferred_tags,
                preferred_categories=preferred_categories,
                liked_place_ids=liked_place_ids
            )
            
            content_recs = self.content_model.recommend(
                user_profile=user_profile,
                top_k=100,
                exclude_ids=exclude_ids,
                category_filter=category_filter
            )
            content_scores = {pid: score for pid, score in content_recs}
        
        # 2. Collaborative scores
        collab_scores = {}
        if user_id and self.collab_model.user_factors is not None:
            collab_recs = self.collab_model.recommend_for_user(
                user_id=user_id,
                top_k=100,
                exclude_ids=exclude_ids
            )
            collab_scores = {pid: score for pid, score in collab_recs}
        
        # 3. Popularity scores
        popularity_scores = self._calculate_popularity_scores(exclude_ids)
        
        # Merge scores
        all_place_ids = set(content_scores.keys()) | set(collab_scores.keys()) | set(popularity_scores.keys())
        
        final_scores = []
        for pid in all_place_ids:
            if pid in exclude_ids:
                continue
            
            c_score = self._normalize_score(content_scores.get(pid, 0), content_scores.values())
            cf_score = self._normalize_score(collab_scores.get(pid, 0), collab_scores.values())
            p_score = self._normalize_score(popularity_scores.get(pid, 0), popularity_scores.values())
            
            weights = self._adjust_weights(
                has_content=bool(preferred_tags or liked_place_ids),
                has_collab=bool(user_id and collab_scores)
            )
            
            final = (
                c_score * weights['content'] +
                cf_score * weights['collaborative'] +
                p_score * weights['popularity']
            )
            
            if pid in self.places_by_id:
                final_scores.append((
                    self.places_by_id[pid],
                    final,
                    {'content': c_score, 'collaborative': cf_score, 'popularity': p_score}
                ))
        
        final_scores.sort(key=lambda x: x[1], reverse=True)
        return final_scores[:top_k]
    
    def get_place_score(self, place_id: int, preferred_tags: List[str] = None) -> float:
        """Lấy AI score cho 1 địa điểm cụ thể."""
        if not self.is_trained:
            return 0.0
        
        try:
            recommendations = self.recommend(
                preferred_tags=preferred_tags or [],
                top_k=200
            )
            
            for place, score, _ in recommendations:
                pid = getattr(place, 'id', None) or getattr(place, 'place_id', None)
                if pid == place_id:
                    return score
        except Exception:
            pass
        
        return 0.0
    
    def _calculate_popularity_scores(self, exclude_ids: List[int]) -> Dict[int, float]:
        """Tính popularity scores."""
        scores = {}
        
        for pid, place in self.places_by_id.items():
            if pid in exclude_ids:
                continue
            
            rating = getattr(place, 'rating', None) or 3.0
            reviews = getattr(place, 'reviewCount', None) or getattr(place, 'review_count', None) or 0
            popularity = getattr(place, 'popularity', None) or 50
            
            score = (
                (rating / 5.0) * 0.4 +
                min(reviews / 100, 1.0) * 0.3 +
                (popularity / 100) * 0.3
            )
            
            scores[pid] = score
        
        return scores
    
    def _normalize_score(self, score: float, all_scores) -> float:
        """Normalize score về 0-1."""
        if not all_scores:
            return 0.5
        
        scores_list = list(all_scores)
        if not scores_list:
            return 0.5
            
        min_s = min(scores_list)
        max_s = max(scores_list)
        
        if max_s == min_s:
            return 0.5
        
        return (score - min_s) / (max_s - min_s)
    
    def _adjust_weights(self, has_content: bool, has_collab: bool) -> Dict[str, float]:
        """Điều chỉnh weights dựa trên data availability."""
        if has_content and has_collab:
            return {
                'content': self.config.content_weight,
                'collaborative': self.config.collaborative_weight,
                'popularity': self.config.popularity_weight
            }
        elif has_content:
            return {'content': 0.6, 'collaborative': 0.0, 'popularity': 0.4}
        elif has_collab:
            return {'content': 0.0, 'collaborative': 0.6, 'popularity': 0.4}
        else:
            return {'content': 0.0, 'collaborative': 0.0, 'popularity': 1.0}
    
    def save_models(self):
        """Lưu cả hai models."""
        self.content_model.save_model()
        if self.collab_model.user_factors is not None:
            self.collab_model.save_model()
    
    def load_models(self) -> bool:
        """Load models."""
        content_loaded = self.content_model.load_model()
        collab_loaded = self.collab_model.load_model()
        self.is_trained = content_loaded
        return content_loaded