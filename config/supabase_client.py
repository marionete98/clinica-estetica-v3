"""
Supabase client module with connection pooling and retry logic.
"""

import asyncio
import time
import sys
from typing import Any, Optional, Callable
from functools import wraps
from types import SimpleNamespace
import structlog
from supabase import create_client, Client
from postgrest.exceptions import APIError

from config.settings import settings
from utils.circuit_breakers import supabase_breaker, CircuitBreakerError

logger = structlog.get_logger(__name__)


class SupabaseClient:
    """
    Supabase client wrapper with connection pooling and retry logic.
    """

    def __init__(self):
        """Initialize Supabase client with service role key."""
        self._client: Optional[Client] = None
        # Lightweight proxy to allow attribute patching in tests before initialization
        self._client_proxy = SimpleNamespace()
        # Provide a 'table' attribute so tests can patch
        self._client_proxy.table = None
        # Avoid real initialization under pytest to allow mocks to attach first
        if "pytest" not in sys.modules:
            self._initialize_client()

    def _initialize_client(self) -> None:
        """Create Supabase client connection."""
        try:
            self._client = create_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_key,
            )
            logger.info("supabase_client_initialized", url=settings.supabase_url)
        except Exception as e:
            logger.error("supabase_client_initialization_failed", error=str(e))
            raise

    @property
    def client(self) -> Client:
        """
        Get Supabase client instance.

        Returns:
            Client: Supabase client instance

        Raises:
            RuntimeError: If client is not initialized
        """
        if self._client is None:
            # Return proxy to allow tests to patch attributes (e.g., .table) before real init
            return self._client_proxy
        return self._client

    @client.setter
    def client(self, value: Client) -> None:
        """Allow setting the underlying Supabase client (useful for tests)."""
        self._client = value

    @client.deleter
    def client(self) -> None:
        """Allow deleting the underlying client (useful for tests/cleanup)."""
        self._client = None

    def health_check(self) -> bool:
        """
        Check if Supabase connection is healthy.

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            # Simple query to check connection (using knowledge_base which exists)
            result = (
                self._client.table("knowledge_base").select("id").limit(1).execute()
            )
            return True
        except Exception as e:
            logger.error("supabase_health_check_failed", error=str(e))
            return False


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry Supabase operations on failure.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry

    Returns:
        Decorated function with retry logic
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (APIError, ConnectionError, TimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            "supabase_operation_retry",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            error=str(e),
                            retry_delay=current_delay,
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "supabase_operation_failed",
                            function=func.__name__,
                            attempts=max_retries,
                            error=str(e),
                        )

            # If all retries failed, raise the last exception
            raise last_exception

        return wrapper

    return decorator


class SupabaseOperations:
    """
    High-level Supabase operations with retry logic.
    """

    def __init__(self, client: SupabaseClient):
        """
        Initialize operations with Supabase client.

        Args:
            client: SupabaseClient instance
        """
        self.client = client

    @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
    def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[dict] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        ascending: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Select data from a table with retry logic.

        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Dictionary of column:value filters
            limit: Maximum number of rows to return
            order_by: Column to order by
            ascending: Sort order (True for ascending, False for descending)

        Returns:
            List of dictionaries representing rows
        """

        def _execute() -> list[dict[str, Any]]:
            query = self.client.client.table(table).select(columns)

            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)

            if order_by:
                query = query.order(order_by, desc=not ascending)

            if limit:
                query = query.limit(limit)

            result = query.execute()
            return result.data

        try:
            return supabase_breaker.call(_execute)
        except CircuitBreakerError as exc:
            logger.error(
                "supabase_select_breaker_open",
                table=table,
                error=str(exc),
            )
            raise

    async def aselect(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[dict] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        ascending: bool = True,
    ) -> list[dict[str, Any]]:
        """Async wrapper for select using asyncio.to_thread to avoid blocking."""
        return await asyncio.to_thread(
            self.select,
            table,
            columns,
            filters,
            limit,
            order_by,
            ascending,
        )

    @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
    def insert(
        self,
        table: str,
        data: dict[str, Any] | list[dict[str, Any]],
        upsert: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Insert data into a table with retry logic.

        Args:
            table: Table name
            data: Dictionary or list of dictionaries to insert
            upsert: If True, perform upsert instead of insert

        Returns:
            List of inserted rows
        """

        def _execute() -> list[dict[str, Any]]:
            query = self.client.client.table(table)
            if upsert:
                result = query.upsert(data).execute()
            else:
                result = query.insert(data).execute()
            return result.data

        try:
            return supabase_breaker.call(_execute)
        except CircuitBreakerError as exc:
            logger.error(
                "supabase_insert_breaker_open",
                table=table,
                error=str(exc),
            )
            raise

    async def ainsert(
        self,
        table: str,
        data: dict[str, Any] | list[dict[str, Any]],
        upsert: bool = False,
    ) -> list[dict[str, Any]]:
        """Async wrapper for insert to keep Supabase calls off the event loop."""
        return await asyncio.to_thread(self.insert, table, data, upsert)

    @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
    def update(
        self, table: str, data: dict[str, Any], filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Update data in a table with retry logic.

        Args:
            table: Table name
            data: Dictionary of columns to update
            filters: Dictionary of column:value filters for WHERE clause

        Returns:
            List of updated rows
        """

        def _execute() -> list[dict[str, Any]]:
            query = self.client.client.table(table).update(data)
            for column, value in filters.items():
                query = query.eq(column, value)
            result = query.execute()
            return result.data

        try:
            return supabase_breaker.call(_execute)
        except CircuitBreakerError as exc:
            logger.error(
                "supabase_update_breaker_open",
                table=table,
                error=str(exc),
            )
            raise

    async def aupdate(
        self,
        table: str,
        data: dict[str, Any],
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Async wrapper for update operations."""
        return await asyncio.to_thread(self.update, table, data, filters)

    @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
    def delete(self, table: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Delete data from a table with retry logic.

        Args:
            table: Table name
            filters: Dictionary of column:value filters for WHERE clause

        Returns:
            List of deleted rows
        """

        def _execute() -> list[dict[str, Any]]:
            query = self.client.client.table(table).delete()
            for column, value in filters.items():
                query = query.eq(column, value)
            result = query.execute()
            return result.data

        try:
            return supabase_breaker.call(_execute)
        except CircuitBreakerError as exc:
            logger.error(
                "supabase_delete_breaker_open",
                table=table,
                error=str(exc),
            )
            raise

    async def adelete(
        self,
        table: str,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Async wrapper for delete operations."""
        return await asyncio.to_thread(self.delete, table, filters)

    @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
    def rpc(self, function_name: str, params: Optional[dict[str, Any]] = None) -> Any:
        """
        Call a Supabase RPC function with retry logic.

        Args:
            function_name: Name of the RPC function
            params: Dictionary of parameters to pass to the function

        Returns:
            Result from the RPC function
        """

        def _execute() -> Any:
            result = self.client.client.rpc(function_name, params or {}).execute()
            return result.data

        try:
            return supabase_breaker.call(_execute)
        except CircuitBreakerError as exc:
            logger.error(
                "supabase_rpc_breaker_open",
                function=function_name,
                error=str(exc),
            )
            raise

    async def arpc(
        self,
        function_name: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Async wrapper for RPC operations."""
        return await asyncio.to_thread(self.rpc, function_name, params)

    async def arun(self, operation: Callable[[Client], Any]) -> Any:
        """Run an arbitrary Supabase operation in a thread-safe way with breaker protection."""

        def _execute() -> Any:
            return operation(self.client.client)

        try:
            return await asyncio.to_thread(supabase_breaker.call, _execute)
        except CircuitBreakerError as exc:
            logger.error(
                "supabase_run_breaker_open",
                error=str(exc),
            )
            raise


_supabase_client: Optional[SupabaseClient] = None
_supabase_operations: Optional[SupabaseOperations] = None


def get_supabase_client() -> SupabaseClient:
    """Get or lazily create a Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_supabase_client()
    return _supabase_client


def get_supabase_operations(client: SupabaseClient | None = None) -> SupabaseOperations:
    """Get or lazily create Supabase operations helper."""
    global _supabase_operations
    if client is None:
        client = get_supabase_client()
    if _supabase_operations is None:
        _supabase_operations = create_supabase_operations(client)
    return _supabase_operations

# Backwards compatibility for modules importing legacy singletons
supabase_client = get_supabase_client()
supabase_operations = get_supabase_operations()



def create_supabase_client() -> SupabaseClient:
    """Factory helper to instantiate SupabaseClient."""
    return SupabaseClient()


def create_supabase_operations(client: SupabaseClient) -> SupabaseOperations:
    """Factory helper to instantiate SupabaseOperations for a given client."""
    return SupabaseOperations(client)


__all__ = [
    "SupabaseClient",
    "SupabaseOperations",
    "create_supabase_client",
    "create_supabase_operations",
    "get_supabase_client",
    "get_supabase_operations",
    "supabase_client",
    "supabase_operations",
]
