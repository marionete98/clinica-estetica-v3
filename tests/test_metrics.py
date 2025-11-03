"""
Unit tests for metrics calculation functions.
Tests P95 latency, handover rate, conversion rate, and cost per conversation.
Requirements: 8.1, 8.2
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ============================================================================
# P95 LATENCY TESTS
# ============================================================================

class TestP95Latency:
    """Tests for P95 latency calculation."""
    
    @pytest.mark.asyncio
    async def test_calculate_p95_latency_basic(self):
        """Test basic P95 latency calculation."""
        from services.metrics import calculate_p95_latency
        
        # Mock logs with latencies: [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        mock_logs = [
            {"latency_ms": 100},
            {"latency_ms": 200},
            {"latency_ms": 300},
            {"latency_ms": 400},
            {"latency_ms": 500},
            {"latency_ms": 600},
            {"latency_ms": 700},
            {"latency_ms": 800},
            {"latency_ms": 900},
            {"latency_ms": 1000},
        ]
        
        mock_response = MagicMock()
        mock_response.data = mock_logs
        
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.not_.is_.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        
        with patch('services.metrics.supabase_client.client', mock_supabase):
            p95 = await calculate_p95_latency(minutes=10)
            
            # P95 of 10 values should be the 9th value (index 9)
            # But since we're using int(len * 0.95), it's index 9
            assert p95 == 1000.0
    
    @pytest.mark.asyncio
    async def test_calculate_p95_latency_no_data(self):
        """Test P95 calculation with no data."""
        from services.metrics import calculate_p95_latency
        
        mock_response = MagicMock()
        mock_response.data = []
        
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.not_.is_.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        
        with patch('services.metrics.supabase_client.client', mock_supabase):
            p95 = await calculate_p95_latency(minutes=10)
            
            assert p95 is None
    
    @pytest.mark.asyncio
    async def test_calculate_p95_latency_single_value(self):
        """Test P95 calculation with single value."""
        from services.metrics import calculate_p95_latency
        
        mock_logs = [{"latency_ms": 500}]
        
        mock_response = MagicMock()
        mock_response.data = mock_logs
        
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.not_.is_.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        
        with patch('services.metrics.supabase_client.client', mock_supabase):
            p95 = await calculate_p95_latency(minutes=10)
            
            assert p95 == 500.0


# ============================================================================
# HANDOVER RATE TESTS
# ============================================================================

class TestHandoverRate:
    """Tests for handover rate calculation."""
    
    @pytest.mark.asyncio
    async def test_calculate_handover_rate_basic(self):
        """Test basic handover rate calculation."""
        from services.metrics import calculate_handover_rate
        
        # Mock 10 total conversations, 2 escalations = 20%
        mock_total_logs = [
            {"conversation_id": f"conv_{i}"} for i in range(10)
        ]
        
        mock_escalation_logs = [
            {"conversation_id": "conv_0"},
            {"conversation_id": "conv_5"},
        ]
        
        mock_supabase = MagicMock()
        
        def mock_table_chain(table_name):
            mock_table = MagicMock()
            mock_table.select.return_value = mock_table
            mock_table.gte.return_value = mock_table
            mock_table.in_.return_value = mock_table
            mock_table.eq.return_value = mock_table
            
            # Return different data based on query
            if hasattr(mock_table, '_is_escalation_query'):
                mock_response = MagicMock()
                mock_response.data = mock_escalation_logs
                mock_table.execute.return_value = mock_response
            else:
                mock_response = MagicMock()
                mock_response.data = mock_total_logs
                mock_table.execute.return_value = mock_response
            
            return mock_table
        
        mock_supabase.table.side_effect = mock_table_chain
        
        with patch('services.metrics.supabase_client.client', mock_supabase):
            # Need to mock both queries
            with patch('services.metrics.supabase_client.client.table') as mock_table_func:
                # First call: total conversations
                total_response = MagicMock()
                total_response.data = mock_total_logs
                
                # Second call: escalations
                escalation_response = MagicMock()
                escalation_response.data = mock_escalation_logs
                
                mock_chain = MagicMock()
                mock_chain.select.return_value = mock_chain
                mock_chain.gte.return_value = mock_chain
                mock_chain.in_.return_value = mock_chain
                mock_chain.eq.return_value = mock_chain
                
                # Configure to return different responses
                mock_chain.execute.side_effect = [total_response, escalation_response]
                mock_table_func.return_value = mock_chain
                
                rate = await calculate_handover_rate(hours=1)
                
                # 2 escalations / 10 total = 20%
                assert rate == 20.0
    
    @pytest.mark.asyncio
    async def test_calculate_handover_rate_no_data(self):
        """Test handover rate with no data."""
        from services.metrics import calculate_handover_rate
        
        mock_response = MagicMock()
        mock_response.data = []
        
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.in_.return_value = mock_table
        mock_table.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        
        with patch('services.metrics.supabase_client.client', mock_supabase):
            rate = await calculate_handover_rate(hours=1)
            
            assert rate is None
    
    @pytest.mark.asyncio
    async def test_calculate_handover_rate_zero_escalations(self):
        """Test handover rate with zero escalations."""
        from services.metrics import calculate_handover_rate
        
        mock_total_logs = [{"conversation_id": f"conv_{i}"} for i in range(10)]
        mock_escalation_logs = []
        
        mock_supabase = MagicMock()
        
        with patch('services.metrics.supabase_client.client.table') as mock_table_func:
            total_response = MagicMock()
            total_response.data = mock_total_logs
            
            escalation_response = MagicMock()
            escalation_response.data = mock_escalation_logs
            
            mock_chain = MagicMock()
            mock_chain.select.return_value = mock_chain
            mock_chain.gte.return_value = mock_chain
            mock_chain.in_.return_value = mock_chain
            mock_chain.eq.return_value = mock_chain
            mock_chain.execute.side_effect = [total_response, escalation_response]
            mock_table_func.return_value = mock_chain
            
            rate = await calculate_handover_rate(hours=1)
            
            # 0 escalations / 10 total = 0%
            assert rate == 0.0


# ============================================================================
# CONVERSION RATE TESTS
# ============================================================================

class TestConversionRate:
    """Tests for booking conversion rate calculation."""
    
    @pytest.mark.asyncio
    async def test_calculate_conversion_rate_basic(self):
        """Test basic conversion rate calculation."""
        from services.metrics import calculate_booking_conversion_rate
        
        # Mock 10 schedule intents, 7 bookings = 70%
        mock_schedule_logs = [{"conversation_id": f"conv_{i}"} for i in range(10)]
        mock_appointments = [{"conversation_id": f"conv_{i}"} for i in range(7)]
        
        with patch('services.metrics.supabase_client.client.table') as mock_table_func:
            schedule_response = MagicMock()
            schedule_response.data = mock_schedule_logs
            
            appointments_response = MagicMock()
            appointments_response.data = mock_appointments
            
            mock_chain = MagicMock()
            mock_chain.select.return_value = mock_chain
            mock_chain.gte.return_value = mock_chain
            mock_chain.eq.return_value = mock_chain
            mock_chain.not_.is_.return_value = mock_chain
            mock_chain.execute.side_effect = [schedule_response, appointments_response]
            mock_table_func.return_value = mock_chain
            
            rate = await calculate_booking_conversion_rate(hours=24)
            
            # 7 bookings / 10 schedule intents = 70%
            assert rate == 70.0
    
    @pytest.mark.asyncio
    async def test_calculate_conversion_rate_no_schedules(self):
        """Test conversion rate with no schedule intents."""
        from services.metrics import calculate_booking_conversion_rate
        
        mock_response = MagicMock()
        mock_response.data = []
        
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        
        with patch('services.metrics.supabase_client.client', mock_supabase):
            rate = await calculate_booking_conversion_rate(hours=24)
            
            assert rate is None
    
    @pytest.mark.asyncio
    async def test_calculate_conversion_rate_perfect(self):
        """Test conversion rate with 100% conversion."""
        from services.metrics import calculate_booking_conversion_rate
        
        mock_schedule_logs = [{"conversation_id": f"conv_{i}"} for i in range(5)]
        mock_appointments = [{"conversation_id": f"conv_{i}"} for i in range(5)]
        
        with patch('services.metrics.supabase_client.client.table') as mock_table_func:
            schedule_response = MagicMock()
            schedule_response.data = mock_schedule_logs
            
            appointments_response = MagicMock()
            appointments_response.data = mock_appointments
            
            mock_chain = MagicMock()
            mock_chain.select.return_value = mock_chain
            mock_chain.gte.return_value = mock_chain
            mock_chain.eq.return_value = mock_chain
            mock_chain.not_.is_.return_value = mock_chain
            mock_chain.execute.side_effect = [schedule_response, appointments_response]
            mock_table_func.return_value = mock_chain
            
            rate = await calculate_booking_conversion_rate(hours=24)
            
            assert rate == 100.0


# ============================================================================
# COST PER CONVERSATION TESTS
# ============================================================================

class TestCostPerConversation:
    """Tests for cost per conversation calculation."""
    
    @pytest.mark.asyncio
    async def test_calculate_cost_per_conversation_basic(self):
        """Test basic cost per conversation calculation."""
        from services.metrics import calculate_cost_per_conversation
        
        # Mock 5 conversations with costs: 0.01, 0.02, 0.03, 0.04, 0.05
        # Total: 0.15, Average: 0.03
        mock_logs = [
            {"conversation_id": "conv_1", "cost_estimate": "0.01"},
            {"conversation_id": "conv_1", "cost_estimate": "0.01"},  # Same conv
            {"conversation_id": "conv_2", "cost_estimate": "0.02"},
            {"conversation_id": "conv_3", "cost_estimate": "0.03"},
            {"conversation_id": "conv_4", "cost_estimate": "0.04"},
            {"conversation_id": "conv_5", "cost_estimate": "0.05"},
        ]
        
        mock_response = MagicMock()
        mock_response.data = mock_logs
        
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.not_.is_.return_value = mock_table
        mock_table.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        
        with patch('services.metrics.supabase_client.client', mock_supabase):
            cost = await calculate_cost_per_conversation(hours=24)
            
            # Total: 0.16, Unique conversations: 5, Average: 0.032
            assert cost == 0.032
    
    @pytest.mark.asyncio
    async def test_calculate_cost_per_conversation_no_data(self):
        """Test cost calculation with no data."""
        from services.metrics import calculate_cost_per_conversation
        
        mock_response = MagicMock()
        mock_response.data = []
        
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.not_.is_.return_value = mock_table
        mock_table.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        
        with patch('services.metrics.supabase_client.client', mock_supabase):
            cost = await calculate_cost_per_conversation(hours=24)
            
            assert cost is None
    
    @pytest.mark.asyncio
    async def test_calculate_cost_per_conversation_single(self):
        """Test cost calculation with single conversation."""
        from services.metrics import calculate_cost_per_conversation
        
        mock_logs = [
            {"conversation_id": "conv_1", "cost_estimate": "0.05"},
        ]
        
        mock_response = MagicMock()
        mock_response.data = mock_logs
        
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.not_.is_.return_value = mock_table
        mock_table.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        
        with patch('services.metrics.supabase_client.client', mock_supabase):
            cost = await calculate_cost_per_conversation(hours=24)
            
            assert cost == 0.05


# ============================================================================
# ERROR RATE TESTS
# ============================================================================

class TestErrorRate:
    """Tests for error rate calculation."""
    
    @pytest.mark.asyncio
    async def test_calculate_error_rate_basic(self):
        """Test basic error rate calculation."""
        from services.metrics import calculate_error_rate
        
        # Mock 10 total logs, 2 with errors = 20%
        mock_supabase = MagicMock()
        
        with patch('services.metrics.supabase_client.client.table') as mock_table_func:
            # First call: total count
            total_response = MagicMock()
            total_response.count = 10
            
            # Second call: error count
            error_response = MagicMock()
            error_response.count = 2
            
            mock_chain = MagicMock()
            mock_chain.select.return_value = mock_chain
            mock_chain.gte.return_value = mock_chain
            mock_chain.not_.is_.return_value = mock_chain
            mock_chain.execute.side_effect = [total_response, error_response]
            mock_table_func.return_value = mock_chain
            
            rate = await calculate_error_rate(minutes=10)
            
            # 2 errors / 10 total = 20%
            assert rate == 20.0
    
    @pytest.mark.asyncio
    async def test_calculate_error_rate_no_data(self):
        """Test error rate with no data."""
        from services.metrics import calculate_error_rate
        
        with patch('services.metrics.supabase_client.client.table') as mock_table_func:
            total_response = MagicMock()
            total_response.count = 0
            
            mock_chain = MagicMock()
            mock_chain.select.return_value = mock_chain
            mock_chain.gte.return_value = mock_chain
            mock_chain.execute.return_value = total_response
            mock_table_func.return_value = mock_chain
            
            rate = await calculate_error_rate(minutes=10)
            
            assert rate is None
    
    @pytest.mark.asyncio
    async def test_calculate_error_rate_zero_errors(self):
        """Test error rate with zero errors."""
        from services.metrics import calculate_error_rate
        
        with patch('services.metrics.supabase_client.client.table') as mock_table_func:
            total_response = MagicMock()
            total_response.count = 10
            
            error_response = MagicMock()
            error_response.count = 0
            
            mock_chain = MagicMock()
            mock_chain.select.return_value = mock_chain
            mock_chain.gte.return_value = mock_chain
            mock_chain.not_.is_.return_value = mock_chain
            mock_chain.execute.side_effect = [total_response, error_response]
            mock_table_func.return_value = mock_chain
            
            rate = await calculate_error_rate(minutes=10)
            
            assert rate == 0.0


# ============================================================================
# AGGREGATE METRICS TESTS
# ============================================================================

class TestAggregateMetrics:
    """Tests for aggregate metrics functions."""
    
    @pytest.mark.asyncio
    async def test_get_all_metrics(self):
        """Test getting all metrics at once."""
        from services.metrics import get_all_metrics
        
        with patch('services.metrics.calculate_p95_latency', return_value=3500.0):
            with patch('services.metrics.calculate_average_latency', return_value=2000.0):
                with patch('services.metrics.calculate_handover_rate', return_value=15.0):
                    with patch('services.metrics.calculate_booking_conversion_rate', return_value=75.0):
                        with patch('services.metrics.calculate_cost_per_conversation', return_value=0.25):
                            with patch('services.metrics.calculate_total_cost', return_value=5.0):
                                with patch('services.metrics.calculate_error_rate', return_value=1.5):
                                    with patch('services.metrics.get_recent_errors', return_value=[]):
                                        metrics = await get_all_metrics()
                                        
                                        assert metrics['p95_latency_ms'] == 3500.0
                                        assert metrics['avg_latency_ms'] == 2000.0
                                        assert metrics['handover_rate_percent'] == 15.0
                                        assert metrics['conversion_rate_percent'] == 75.0
                                        assert metrics['cost_per_conversation_brl'] == 0.25
                                        assert metrics['total_cost_brl'] == 5.0
                                        assert metrics['error_rate_percent'] == 1.5
                                        assert 'timestamp' in metrics
    
    @pytest.mark.asyncio
    async def test_get_metrics_summary(self):
        """Test getting core metrics summary."""
        from services.metrics import get_metrics_summary
        
        with patch('services.metrics.calculate_p95_latency', return_value=3500.0):
            with patch('services.metrics.calculate_handover_rate', return_value=15.0):
                with patch('services.metrics.calculate_booking_conversion_rate', return_value=75.0):
                    with patch('services.metrics.calculate_cost_per_conversation', return_value=0.25):
                        summary = await get_metrics_summary()
                        
                        assert summary['p95_latency_ms'] == 3500.0
                        assert summary['handover_rate_percent'] == 15.0
                        assert summary['conversion_rate_percent'] == 75.0
                        assert summary['cost_per_conversation_brl'] == 0.25
                        assert 'timestamp' in summary


# ============================================================================
# RECENT ERRORS TESTS
# ============================================================================

class TestRecentErrors:
    """Tests for recent errors retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_recent_errors(self):
        """Test getting recent error logs."""
        from services.metrics import get_recent_errors
        
        mock_errors = [
            {
                "ts": "2025-10-16T10:00:00Z",
                "conversation_id": "conv_1",
                "intent": "schedule",
                "error_message": "Calendar API timeout",
                "provider": "grok"
            },
            {
                "ts": "2025-10-16T09:55:00Z",
                "conversation_id": "conv_2",
                "intent": "faq",
                "error_message": "LLM timeout",
                "provider": "gemini"
            }
        ]
        
        mock_response = MagicMock()
        mock_response.data = mock_errors
        
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.not_.is_.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        
        with patch('services.metrics.supabase_client.client', mock_supabase):
            errors = await get_recent_errors(limit=10)
            
            assert len(errors) == 2
            assert errors[0]['error_message'] == "Calendar API timeout"
            assert errors[1]['provider'] == "gemini"
    
    @pytest.mark.asyncio
    async def test_get_recent_errors_empty(self):
        """Test getting recent errors when none exist."""
        from services.metrics import get_recent_errors
        
        mock_response = MagicMock()
        mock_response.data = []
        
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.not_.is_.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        mock_supabase.table.return_value = mock_table
        
        with patch('services.metrics.supabase_client.client', mock_supabase):
            errors = await get_recent_errors(limit=10)
            
            assert errors == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
