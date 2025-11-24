"""Repository factory for selecting appropriate implementation"""
import os
import logging
from app.application.interfaces.place_repository import IPlaceRepository

logger = logging.getLogger(__name__)


def get_place_repository() -> IPlaceRepository:
    """
    Factory method to get the appropriate repository implementation
    
    Returns:
        MySQLPlaceRepository if DB_HOST is configured, otherwise InMemoryPlaceRepository
    """
    db_host = os.getenv("DB_HOST")
    
    if db_host:
        try:
            from .mysql_place_repo import MySQLPlaceRepository
            logger.info("Using MySQL place repository")
            return MySQLPlaceRepository()
        except Exception as e:
            logger.error(f"Failed to initialize MySQL repository: {e}")
            logger.warning("Falling back to in-memory repository")
    
    from .in_memory_place_repository import InMemoryPlaceRepository
    logger.info("Using in-memory place repository")
    return InMemoryPlaceRepository()


__all__ = ['get_place_repository']
