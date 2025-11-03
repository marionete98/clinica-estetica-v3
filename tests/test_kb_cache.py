"""
Tests for Redis Knowledge Base Cache implementation.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from services.kb_cache_service import KnowledgeBaseCacheService, CacheStats


class TestKnowledgeBaseCacheService:
    """Test the knowledge base cache service."""
    
    @pytest.fixture
    def cache_service(self):
        """Create a cache service instance for testing."""
        return KnowledgeBaseCacheService()
    
    def test_cache_service_initialization(self, cache_service):
        """Test cache service initializes correctly."""
        assert cache_service.KB_PREFIX == "kb:"
        assert cache_service.TEMPLATE_PREFIX == "template:"
        assert cache_service.CACHE_TTL == 4 * 60 * 60
        assert cache_service.SYNC_INTERVAL == 3 * 60 * 60
        assert cache_service._stats["hits"] == 0
        assert cache_service._stats["misses"] == 0
    
    def test_calculate_relevance_score(self, cache_service):
        """Test relevance score calculation."""
        entry = {
            "title": "Depilação a Laser - Informações Gerais",
            "content": "Tecnologia: Laser Galaxy Fiber. Remove pelos de forma definitiva.",
            "keywords": ["laser", "depilação", "remoção"]
        }
        
        keywords = ["laser", "depilação"]
        original_query = "depilação laser"
        
        score = cache_service._calculate_relevance_score(entry, keywords, original_query)
        
        # Should have high score due to title matches and keyword matches
        assert score > 5.0
    
    def test_score_entries_sorting(self, cache_service):
        """Test that entries are sorted by relevance score."""
        entries = [
            {
                "title": "Harmonização Facial",
                "content": "Procedimentos estéticos faciais",
                "keywords": ["harmonização", "facial"]
            },
            {
                "title": "Depilação a Laser",
                "content": "Remoção de pelos com laser",
                "keywords": ["laser", "depilação"]
            }
        ]
        
        keywords = ["laser", "depilação"]
        original_query = "depilação laser"
        
        scored_entries = cache_service._score_entries(entries, keywords, original_query)
        
        # First entry should have higher score (better match)
        assert scored_entries[0]["title"] == "Depilação a Laser"
        assert scored_entries[0]["relevance_score"] > scored_entries[1]["relevance_score"]
    
    async def test_get_cache_stats(self, cache_service):
        """Test cache statistics generation."""
        # Mock Redis keys
        with patch.object(cache_service.redis.client, 'keys') as mock_keys:
            mock_keys.side_effect = [
                ["kb:entry1", "kb:entry2"],  # KB keys
                ["template:temp1"]           # Template keys
            ]

            # Set some stats
            cache_service._stats["hits"] = 100
            cache_service._stats["misses"] = 10

            stats = await cache_service.get_cache_stats()

        assert isinstance(stats, CacheStats)
        assert stats.total_entries == 2
        assert stats.total_templates == 1
        assert stats.cache_hits == 100
        assert stats.cache_misses == 10
        assert abs(stats.hit_rate - 0.909) < 0.01  # Approximately 100/110


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])