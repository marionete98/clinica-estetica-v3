"""
Knowledge Base Cache Service for Redis-based caching with automatic synchronization.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

import numpy as np

from config.redis_client import RedisClient
from config.supabase_client import SupabaseClient
from models.repositories.knowledge_base import (
    get_message_template as repo_get_message_template,
    search_knowledge_base as repo_search_knowledge_base,
)
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Statistics for knowledge base cache."""
    total_entries: int
    total_templates: int
    last_sync: Optional[datetime]
    cache_hits: int
    cache_misses: int
    hit_rate: float
    cache_size_mb: float


class KnowledgeBaseCacheService:
    """Redis-based cache service for knowledge base with automatic synchronization."""
    
    # Redis key prefixes
    KB_PREFIX = "kb:"
    TEMPLATE_PREFIX = "template:"
    METADATA_KEY = "kb:metadata"
    
    # Cache TTL (4 hours)
    CACHE_TTL = 4 * 60 * 60
    
    # Sync interval (3 hours)
    SYNC_INTERVAL = 3 * 60 * 60
    
    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        supabase_client: Optional[SupabaseClient] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        """Initialize the knowledge base cache service."""
        self.redis = redis_client or RedisClient()
        self._supabase_client = supabase_client or SupabaseClient()
        self._embedding_service = embedding_service or EmbeddingService()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "searches": 0,
            "template_requests": 0
        }
        self._embedding_weight = 5.0
        
        logger.info("Knowledge Base Cache Service initialized")
    
    async def initialize_cache(self) -> bool:
        """Initialize cache by loading all data from Supabase."""
        try:
            logger.info("Initializing knowledge base cache...")
            
            # Load knowledge base entries
            kb_success = await self._sync_knowledge_base()
            
            # Load message templates
            template_success = await self._sync_message_templates()
            
            if kb_success and template_success:
                await self._update_cache_metadata()
                logger.info("Knowledge base cache initialized successfully")
                return True
            else:
                logger.error("Failed to initialize knowledge base cache")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing knowledge base cache: {e}")
            return False
    
    async def sync_cache(self) -> bool:
        """Synchronize cache with Supabase data."""
        try:
            logger.info("Starting knowledge base cache synchronization...")
            
            # Check if sync is needed
            if not await self._should_sync():
                logger.info("Cache sync not needed yet")
                return True
            
            # Sync knowledge base
            kb_success = await self._sync_knowledge_base()
            
            # Sync templates
            template_success = await self._sync_message_templates()
            
            if kb_success and template_success:
                await self._update_cache_metadata()
                logger.info("Knowledge base cache synchronized successfully")
                return True
            else:
                logger.error("Knowledge base cache synchronization failed")
                return False
                
        except Exception as e:
            logger.error(f"Error synchronizing knowledge base cache: {e}")
            return False
    
    async def _should_sync(self) -> bool:
        """Check if cache synchronization is needed."""
        try:
            metadata = await self.redis.get_value(self.METADATA_KEY)

            if not metadata:
                return True

            last_sync = datetime.fromisoformat(metadata.get("last_sync", ""))
            sync_threshold = datetime.now() - timedelta(seconds=self.SYNC_INTERVAL)
            
            return last_sync < sync_threshold
            
        except Exception:
            return True
    
    async def _sync_knowledge_base(self) -> bool:
        """Sync knowledge base entries to Redis."""
        try:
            # Get all knowledge base entries from Supabase
            supabase = self._supabase_client.client
            
            response = supabase.table('knowledge_base').select('*').execute()
            
            if not response.data:
                logger.warning("No knowledge base entries found in Supabase")
                return True
            
            # Clear existing KB cache
            await self._clear_kb_cache()
            
            # Cache each entry
            cached_count = 0
            for entry in response.data:
                cache_entry = self._prepare_cache_entry(entry)
                if not cache_entry:
                    continue

                cache_entry = await self._attach_embedding(cache_entry)

                kb_key = f"{self.KB_PREFIX}{cache_entry['id']}"

                if await self.redis.set_value(kb_key, cache_entry, self.CACHE_TTL):
                    cached_count += 1
                
                # Create keyword index for fast searching
                await self._index_kb_entry(cache_entry)
            
            logger.info(f"Cached {cached_count} knowledge base entries")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing knowledge base: {e}")
            return False
    
    async def _sync_message_templates(self) -> bool:
        """Sync message templates to Redis."""
        try:
            # Get all message templates from Supabase
            supabase = self._supabase_client.client
            
            response = supabase.table('message_templates').select('*').eq('active', True).execute()
            
            if not response.data:
                logger.warning("No message templates found in Supabase")
                return True
            
            # Clear existing template cache
            await self._clear_template_cache()
            
            # Cache each template
            cached_count = 0
            for template in response.data:
                template_key = f"{self.TEMPLATE_PREFIX}{template['name']}"
                
                # Prepare cache entry
                cache_entry = {
                    "id": template["id"],
                    "name": template["name"],
                    "content": template["content"],
                    "variables": template.get("variables", []),
                    "category": template.get("category"),
                    "active": template.get("active", True),
                    "cached_at": datetime.now().isoformat()
                }
                
                # Store in Redis
                if await self.redis.set_value(template_key, cache_entry, self.CACHE_TTL):
                    cached_count += 1
            
            logger.info(f"Cached {cached_count} message templates")
            return True
            
        except Exception as e:
            # Log the error but allow the system to continue
            # Templates are optional - the system can work without them
            error_msg = str(e)
            if "Could not find the table" in error_msg or "PGRST205" in error_msg:
                logger.warning(f"Message templates table not found in Supabase - skipping template sync")
                return True  # Return True to allow KB cache initialization to succeed
            else:
                logger.error(f"Error syncing message templates: {e}")
                return False
    
    async def _index_kb_entry(self, entry: Dict[str, Any]) -> None:
        """Create keyword index for knowledge base entry."""
        try:
            await self.redis.ensure_initialized()
            
            # Extract keywords from title and content
            text = f"{entry['title']} {entry['content']}".lower()
            keywords = set()
            
            # Add explicit keywords
            if entry.get("keywords"):
                keywords.update([kw.lower() for kw in entry["keywords"]])
            
            # Extract words from text (minimum 3 characters)
            words = [word.strip() for word in text.split() if len(word.strip()) >= 3]
            keywords.update(words)
            
            # Create index entries
            for keyword in keywords:
                index_key = f"kb:index:{keyword}"

                # Add entry ID to keyword index (using Redis sets)
                await self.redis.client.sadd(index_key, entry["id"])
                await self.redis.client.expire(index_key, self.CACHE_TTL)
                
        except Exception as e:
            logger.error(f"Error indexing KB entry {entry.get('id')}: {e}")
    
    async def _clear_kb_cache(self) -> None:
        """Clear all knowledge base cache entries."""
        try:
            await self.redis.ensure_initialized()
            
            # Get all KB keys
            kb_keys = await self.redis.client.keys(f"{self.KB_PREFIX}*")
            index_keys = await self.redis.client.keys("kb:index:*")

            # Delete all keys
            all_keys = list(kb_keys) + list(index_keys)
            if all_keys:
                await self.redis.client.delete(*all_keys)

            logger.debug(f"Cleared {len(all_keys)} KB cache entries")

        except Exception as e:
            logger.error(f"Error clearing KB cache: {e}")
    
    async def _clear_template_cache(self) -> None:
        """Clear all template cache entries."""
        try:
            await self.redis.ensure_initialized()
            
            # Get all template keys
            template_keys = await self.redis.client.keys(f"{self.TEMPLATE_PREFIX}*")
            
            # Delete all keys
            if template_keys:
                await self.redis.client.delete(*template_keys)
                
            logger.debug(f"Cleared {len(template_keys)} template cache entries")
            
        except Exception as e:
            logger.error(f"Error clearing template cache: {e}")
    
    async def _update_cache_metadata(self) -> None:
        """Update cache metadata."""
        try:
            metadata = {
                "last_sync": datetime.now().isoformat(),
                "sync_interval": self.SYNC_INTERVAL,
                "cache_ttl": self.CACHE_TTL,
                "version": "1.0"
            }
            
            await self.redis.set_value(self.METADATA_KEY, metadata, self.CACHE_TTL)
            
        except Exception as e:
            logger.error(f"Error updating cache metadata: {e}")

    def _prepare_cache_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize raw KB entry payload into cache format."""
        required_fields = ("id", "title", "content")
        missing = [field for field in required_fields if not entry.get(field)]
        if missing:
            logger.warning(
                "Skipping KB entry missing required fields",
                entry_id=entry.get("id"),
                missing=missing,
            )
            return None

        cache_entry = {
            "id": str(entry["id"]),
            "title": entry["title"],
            "content": entry["content"],
            "category": entry.get("category"),
            "keywords": entry.get("keywords", []),
            "version": entry.get("version", "1.0"),
            "created_at": entry.get("created_at"),
            "updated_at": entry.get("updated_at"),
            "cached_at": entry.get("cached_at", datetime.now().isoformat()),
            "source": entry.get("source", "cache"),
        }
        return cache_entry

    async def _attach_embedding(self, cache_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Compute and attach embedding vector to a cache entry."""
        try:
            text = self._build_embedding_text(cache_entry)
            cache_entry["embedding"] = await self._embedding_service.embed_text(text)
        except Exception as exc:
            logger.error(
                f"Error generating embedding for entry {cache_entry.get('id')}: {exc}"
            )
            cache_entry["embedding"] = []
        return cache_entry

    @staticmethod
    def _build_embedding_text(entry: Dict[str, Any]) -> str:
        """Combine relevant fields to feed the embedding model."""
        title = entry.get("title") or ""
        content = entry.get("content") or ""
        keywords = " ".join(entry.get("keywords", []))
        return " ".join(part for part in [title, content, keywords] if part)

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec_a or not vec_b:
            return 0.0
        try:
            a = np.array(vec_a, dtype=float)
            b = np.array(vec_b, dtype=float)
            if not a.any() or not b.any():
                return 0.0
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
        except Exception:
            return 0.0

    async def upsert_entries(self, entries: List[Dict[str, Any]]) -> bool:
        """Upsert knowledge base entries directly into the Redis cache."""
        if not entries:
            return True

        try:
            await self.redis.ensure_initialized()
            upserted = 0

            for entry in entries:
                cache_entry = self._prepare_cache_entry(entry)
                if not cache_entry:
                    continue

                cache_entry = await self._attach_embedding(cache_entry)

                kb_key = f"{self.KB_PREFIX}{cache_entry['id']}"
                if await self.redis.set_value(kb_key, cache_entry, self.CACHE_TTL):
                    upserted += 1
                await self._index_kb_entry(cache_entry)

            if upserted:
                await self._update_cache_metadata()
                logger.info(f"Upserted {upserted} KB entries directly into cache")
            return True
        except Exception as e:
            logger.error(f"Error upserting KB entries: {e}")
            return False
    
    async def search_knowledge_base(
        self,
        query: str,
        top_k: int = 3,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search knowledge base using cache with lexical + embedding scoring."""
        keywords: List[str] = []
        query_embedding: Optional[List[float]] = None

        try:
            self._stats["searches"] += 1

            keywords = [
                word.lower().strip()
                for word in query.split()
                if len(word.strip()) >= 3
            ]

            try:
                embed_input = " ".join(keywords) if keywords else query
                query_embedding = await self._embedding_service.embed_text(embed_input)
            except Exception as embed_error:
                logger.error(f"Error generating query embedding: {embed_error}")
                query_embedding = None

            logger.debug(
                f"Searching KB cache: query='{query}', keywords={keywords}, top_k={top_k}"
            )

            matching_ids: Set[str] = set()
            if keywords:
                matching_ids = await self._find_matching_entries(keywords)

            if not matching_ids:
                self._stats["misses"] += 1
                logger.debug("No matches in cache, falling back to Supabase")
                return await self._fallback_search(query, top_k, category, query_embedding, keywords)

            entries = await self._get_cached_entries(matching_ids, category)

            if not entries:
                self._stats["misses"] += 1
                return await self._fallback_search(query, top_k, category, query_embedding, keywords)

            scored_entries = self._score_entries(entries, keywords, query, query_embedding)
            results = scored_entries[:top_k]

            self._stats["hits"] += 1
            logger.info(f"Found {len(results)} KB entries in cache for query: {query}")

            return results

        except Exception as e:
            logger.error(f"Error searching KB cache: {e}")
            self._stats["misses"] += 1
            return await self._fallback_search(query, top_k, category, query_embedding, keywords)
    
    async def _find_matching_entries(self, keywords: List[str]) -> Set[str]:
        """Find entry IDs that match keywords using Redis index."""
        try:
            await self.redis.ensure_initialized()
            
            matching_ids = set()
            
            for keyword in keywords:
                index_key = f"kb:index:{keyword}"
                ids = await self.redis.client.smembers(index_key)
                
                if ids:
                    if not matching_ids:
                        # First keyword - initialize set
                        matching_ids = set(ids)
                    else:
                        # Subsequent keywords - union for OR logic
                        matching_ids = matching_ids.union(set(ids))
            
            return matching_ids
            
        except Exception as e:
            logger.error(f"Error finding matching entries: {e}")
            return set()
    
    async def _get_cached_entries(
        self,
        entry_ids: Set[str],
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get cached entries by IDs."""
        entries = []
        
        for entry_id in entry_ids:
            kb_key = f"{self.KB_PREFIX}{entry_id}"
            entry = await self.redis.get_value(kb_key)
            
            if entry:
                # Apply category filter if specified
                if category and entry.get("category") != category:
                    continue
                    
                entries.append(entry)
        
        return entries
    
    def _score_entries(
        self,
        entries: List[Dict[str, Any]],
        keywords: List[str],
        original_query: str,
        query_embedding: Optional[List[float]]
    ) -> List[Dict[str, Any]]:
        """Score and sort entries by relevance."""
        scored_entries: List[Dict[str, Any]] = []

        for entry in entries:
            score = self._calculate_relevance_score(entry, keywords, original_query)

            embedding = entry.get("embedding")
            if query_embedding and embedding:
                vector_score = self._cosine_similarity(query_embedding, embedding)
                entry["vector_score"] = vector_score
                score += self._embedding_weight * vector_score

            entry["relevance_score"] = score
            scored_entries.append(entry)

        scored_entries.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
        return scored_entries
    
    def _calculate_relevance_score(
        self,
        entry: Dict[str, Any],
        keywords: List[str],
        original_query: str
    ) -> float:
        """Calculate relevance score for an entry."""
        score = 0.0
        
        title = entry.get("title", "").lower()
        content = entry.get("content", "").lower()
        entry_keywords = [kw.lower() for kw in entry.get("keywords", [])]
        
        # Title matches (highest weight)
        for keyword in keywords:
            if keyword in title:
                score += 3.0
        
        # Explicit keyword matches (high weight)
        for keyword in keywords:
            if keyword in entry_keywords:
                score += 2.0
        
        # Content matches (medium weight)
        for keyword in keywords:
            if keyword in content:
                score += 1.0
        
        # Exact phrase match bonus
        if original_query.lower() in title:
            score += 5.0
        elif original_query.lower() in content:
            score += 2.0
        
        return score
    
    async def _fallback_search(
        self,
        query: str,
        top_k: int,
        category: Optional[str],
        query_embedding: Optional[List[float]],
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """Fallback to Supabase search when cache fails."""
        try:
            logger.info(f"Using Supabase fallback for query: {query}")

            results = await repo_search_knowledge_base(
                keywords=keywords,
                category=category
            )

            entries: List[Dict[str, Any]] = []
            for kb in results[: max(top_k * 2, top_k)]:
                entry = {
                    "id": str(kb.id),
                    "title": kb.title,
                    "content": kb.content,
                    "category": kb.category,
                    "keywords": kb.keywords or [],
                    "version": kb.version,
                    "created_at": kb.created_at.isoformat() if kb.created_at else None,
                    "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
                    "source": "supabase_fallback"
                }
                entry = await self._attach_embedding(entry)
                entries.append(entry)

            if not entries:
                return []

            scored_entries = self._score_entries(entries, keywords, query, query_embedding)
            return scored_entries[:top_k]

        except Exception as e:
            logger.error(f"Supabase fallback search failed: {e}")
            return []
    
    async def get_message_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get message template from Redis cache."""
        try:
            self._stats["template_requests"] += 1
            
            template_key = f"{self.TEMPLATE_PREFIX}{template_name}"
            template = await self.redis.get_value(template_key)
            
            if template:
                self._stats["hits"] += 1
                logger.debug(f"Retrieved template from cache: {template_name}")
                return template
            else:
                self._stats["misses"] += 1
                logger.debug(f"Template not in cache, falling back to Supabase: {template_name}")
                return await self._fallback_get_template(template_name)
                
        except Exception as e:
            logger.error(f"Error getting template from cache: {e}")
            self._stats["misses"] += 1
            return await self._fallback_get_template(template_name)
    
    async def _fallback_get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Fallback to Supabase for template retrieval."""
        try:
            template = await repo_get_message_template(template_name)
            
            if template:
                return {
                    "id": str(template.id),
                    "name": template.name,
                    "content": template.content,
                    "variables": template.variables or [],
                    "category": template.category,
                    "active": template.active,
                    "source": "supabase_fallback"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Supabase template fallback failed: {e}")
            return None
    
    async def format_template(
        self,
        template_name: str,
        variables: Dict[str, str]
    ) -> Optional[str]:
        """Get and format a message template."""
        try:
            template = await self.get_message_template(template_name)
            
            if not template:
                return None
            
            content = template["content"]
            
            # Replace variables
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                content = content.replace(placeholder, str(var_value))
            
            return content
            
        except Exception as e:
            logger.error(f"Error formatting template: {e}")
            return None
    
    async def get_cache_stats(self) -> CacheStats:
        """Get cache statistics."""
        try:
            await self.redis.ensure_initialized()
            
            # Get metadata
            try:
                metadata = await self.redis.get_value(self.METADATA_KEY) or {}
            except Exception:
                metadata = {}
            # Ensure metadata is a dict
            if not isinstance(metadata, dict):
                metadata = {}

            # Count entries
            kb_keys = await self.redis.client.keys(f"{self.KB_PREFIX}*")
            template_keys = await self.redis.client.keys(f"{self.TEMPLATE_PREFIX}*")

            # Calculate hit rate
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0

            # Estimate cache size (rough approximation)
            cache_size_mb = (len(kb_keys) + len(template_keys)) * 0.001  # Rough estimate

            # Parse last sync
            last_sync = None
            if isinstance(metadata, dict) and metadata.get("last_sync"):
                try:
                    last_sync = datetime.fromisoformat(metadata["last_sync"])
                except ValueError:
                    pass
            
            return CacheStats(
                total_entries=len(kb_keys),
                total_templates=len(template_keys),
                last_sync=last_sync,
                cache_hits=self._stats["hits"],
                cache_misses=self._stats["misses"],
                hit_rate=hit_rate,
                cache_size_mb=cache_size_mb
            )
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return CacheStats(0, 0, None, 0, 0, 0.0, 0.0)
    
    async def invalidate_cache(self) -> bool:
        """Invalidate entire cache and force resync."""
        try:
            logger.info("Invalidating knowledge base cache...")
            
            # Clear all cache
            await self._clear_kb_cache()
            await self._clear_template_cache()
            
            # Clear metadata
            await self.redis.delete_key(self.METADATA_KEY)
            
            # Reset stats
            self._stats = {
                "hits": 0,
                "misses": 0,
                "searches": 0,
                "template_requests": 0
            }
            
            logger.info("Knowledge base cache invalidated")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False


__all__ = ["KnowledgeBaseCacheService", "CacheStats"]
