"""
Unit tests for tool functions.
Tests focus on core business logic without requiring live database connections.
Requirements: 2.1, 2.2, 3.1, 4.2, 4.3, 4.6
"""

import pytest
from datetime import datetime, date, time, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from zoneinfo import ZoneInfo

# Import functions to test
from tools.scheduler_tools import (
    is_within_business_hours,
    generate_time_slots,
    parse_time,
    BUSINESS_HOURS
)
from tools.contact_tools import (
    validate_brazilian_phone,
    normalize_brazilian_phone
)


# ============================================================================
# BUSINESS HOURS TESTS
# ============================================================================

class TestBusinessHours:
    """Tests for business hours validation."""
    
    def test_weekday_within_hours(self):
        """Test that weekday times within business hours are valid."""
        # Monday at 10:00 AM
        dt = datetime(2025, 10, 20, 10, 0)  # Monday
        assert is_within_business_hours(dt) is True
        
        # Friday at 6:00 PM
        dt = datetime(2025, 10, 24, 18, 0)  # Friday
        assert is_within_business_hours(dt) is True
    
    def test_weekday_before_opening(self):
        """Test that times before opening are invalid."""
        # Monday at 8:00 AM (opens at 8:30)
        dt = datetime(2025, 10, 20, 8, 0)
        assert is_within_business_hours(dt) is False
    
    def test_weekday_after_closing(self):
        """Test that times after closing are invalid."""
        # Monday at 7:00 PM (closes at 7:00 PM)
        dt = datetime(2025, 10, 20, 19, 0)
        assert is_within_business_hours(dt) is False
    
    def test_saturday_within_hours(self):
        """Test that Saturday times within hours are valid."""
        # Saturday at 10:00 AM
        dt = datetime(2025, 10, 25, 10, 0)  # Saturday
        assert is_within_business_hours(dt) is True
    
    def test_saturday_after_noon(self):
        """Test that Saturday afternoon is invalid (closes at 12:00)."""
        # Saturday at 1:00 PM
        dt = datetime(2025, 10, 25, 13, 0)
        assert is_within_business_hours(dt) is False
    
    def test_sunday_closed(self):
        """Test that Sunday is closed."""
        # Sunday at 10:00 AM
        dt = datetime(2025, 10, 26, 10, 0)  # Sunday
        assert is_within_business_hours(dt) is False


# ============================================================================
# TIME SLOT GENERATION TESTS
# ============================================================================

class TestTimeSlotGeneration:
    """Tests for time slot generation."""
    
    def test_generate_slots_single_day(self):
        """Test generating slots for a single day."""
        start_date = date(2025, 10, 20)  # Monday
        end_date = date(2025, 10, 20)
        duration_min = 60
        interval_min = 30
        
        slots = generate_time_slots(start_date, end_date, duration_min, interval_min)
        
        # Should have slots from 8:30 to 18:00 (last slot starts at 18:00, ends at 19:00)
        assert len(slots) > 0
        
        # First slot should start at 8:30
        first_slot = slots[0]
        assert first_slot[0].time() == time(8, 30)
        
        # All slots should be on the same day
        for slot_start, slot_end in slots:
            assert slot_start.date() == start_date
            assert slot_end == slot_start + timedelta(minutes=duration_min)
    
    def test_generate_slots_skip_sunday(self):
        """Test that Sunday is skipped when generating slots."""
        # Saturday to Monday
        start_date = date(2025, 10, 25)  # Saturday
        end_date = date(2025, 10, 27)    # Monday
        duration_min = 60
        
        slots = generate_time_slots(start_date, end_date, duration_min)
        
        # Check that no slots are on Sunday
        for slot_start, slot_end in slots:
            assert slot_start.weekday() != 6  # 6 = Sunday
    
    def test_generate_slots_respects_duration(self):
        """Test that slots respect the specified duration."""
        start_date = date(2025, 10, 20)
        end_date = date(2025, 10, 20)
        duration_min = 90
        
        slots = generate_time_slots(start_date, end_date, duration_min)
        
        for slot_start, slot_end in slots:
            actual_duration = (slot_end - slot_start).total_seconds() / 60
            assert actual_duration == duration_min
    
    def test_generate_slots_saturday_half_day(self):
        """Test that Saturday only has morning slots."""
        start_date = date(2025, 10, 25)  # Saturday
        end_date = date(2025, 10, 25)
        duration_min = 60
        
        slots = generate_time_slots(start_date, end_date, duration_min)
        
        # All slots should end by 12:00
        for slot_start, slot_end in slots:
            assert slot_end.time() <= time(12, 0)


# ============================================================================
# PHONE VALIDATION TESTS
# ============================================================================

class TestPhoneValidation:
    """Tests for Brazilian phone number validation."""
    
    def test_validate_phone_with_country_code(self):
        """Test validation of phone with +55 country code."""
        valid_phones = [
            "+5511999999999",
            "+55 11 99999-9999",
            "+55 (11) 99999-9999",
        ]
        
        for phone in valid_phones:
            assert validate_brazilian_phone(phone) is True, f"Failed for: {phone}"
    
    def test_validate_phone_without_country_code(self):
        """Test validation of phone without country code."""
        valid_phones = [
            "11999999999",
            "(11) 99999-9999",
            "11 99999-9999",
        ]
        
        for phone in valid_phones:
            assert validate_brazilian_phone(phone) is True, f"Failed for: {phone}"
    
    def test_validate_phone_landline(self):
        """Test validation of landline numbers (10 digits)."""
        valid_phones = [
            "1133334444",
            "(11) 3333-4444",
            "+55 11 3333-4444",
        ]
        
        for phone in valid_phones:
            assert validate_brazilian_phone(phone) is True, f"Failed for: {phone}"
    
    def test_validate_phone_invalid_formats(self):
        """Test that invalid phone formats are rejected."""
        invalid_phones = [
            "123",              # Too short
            "11999999",         # Too short
            "119999999999",     # Too long
            "00999999999",      # Invalid DDD (starts with 0)
            "abc11999999999",   # Contains letters
            "",                 # Empty
        ]
        
        for phone in invalid_phones:
            assert validate_brazilian_phone(phone) is False, f"Should fail for: {phone}"
    
    def test_normalize_phone_with_country_code(self):
        """Test normalization of phone with country code."""
        phone = "+55 (11) 99999-9999"
        normalized = normalize_brazilian_phone(phone)
        assert normalized == "+5511999999999"
    
    def test_normalize_phone_without_country_code(self):
        """Test normalization of phone without country code."""
        phone = "(11) 99999-9999"
        normalized = normalize_brazilian_phone(phone)
        assert normalized == "+5511999999999"
    
    def test_normalize_phone_invalid_raises_error(self):
        """Test that normalizing invalid phone raises ValueError."""
        with pytest.raises(ValueError):
            normalize_brazilian_phone("invalid")


# ============================================================================
# MOCK-BASED TOOL TESTS
# ============================================================================

class TestListAvailableSlots:
    """Tests for list_available_slots function with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_list_slots_basic(self):
        """Test basic slot listing with mocked service and calendar."""
        from tools.scheduler_tools import list_available_slots
        
        # Mock service
        mock_service = MagicMock()
        mock_service.id = uuid4()
        mock_service.name = "Botox"
        mock_service.duration_min = 60
        mock_service.room_id = None
        mock_service.equipment_id = None
        
        # Mock calendar client
        mock_calendar = AsyncMock()
        mock_calendar.get_appointments = AsyncMock(return_value=[])
        
        with patch('tools.scheduler_tools.get_service_by_id', return_value=mock_service):
            with patch('tools.scheduler_tools.get_calendar_client', return_value=mock_calendar):
                service_id = str(mock_service.id)
                slots = await list_available_slots(service_id, date_range=1)
                
                # Should return some slots
                assert isinstance(slots, list)
                assert len(slots) > 0
                
                # Each slot should have required fields
                for slot in slots:
                    assert 'start_datetime' in slot
                    assert 'end_datetime' in slot
                    assert 'date' in slot
                    assert 'start_time' in slot
                    assert 'end_time' in slot
                    assert 'duration_min' in slot
                    assert slot['duration_min'] == 60
    
    @pytest.mark.asyncio
    async def test_list_slots_filters_conflicts(self):
        """Test that slots with conflicts are filtered out."""
        from tools.scheduler_tools import list_available_slots
        
        # Mock service
        mock_service = MagicMock()
        mock_service.id = uuid4()
        mock_service.name = "Botox"
        mock_service.duration_min = 60
        mock_service.room_id = None
        mock_service.equipment_id = None
        
        # Mock existing appointment at 10:00
        tomorrow = date.today() + timedelta(days=1)
        existing_apt = {
            'id': str(uuid4()),
            'appointment_date': tomorrow.isoformat(),
            'start_time': '10:00',
            'end_time': '11:00',
            'status': 'scheduled'
        }
        
        mock_calendar = AsyncMock()
        mock_calendar.get_appointments = AsyncMock(return_value=[existing_apt])
        
        with patch('tools.scheduler_tools.get_service_by_id', return_value=mock_service):
            with patch('tools.scheduler_tools.get_calendar_client', return_value=mock_calendar):
                service_id = str(mock_service.id)
                slots = await list_available_slots(service_id, date_range=2)
                
                # Check that 10:00 slot is not in available slots
                conflict_time = datetime.combine(tomorrow, time(10, 0))
                for slot in slots:
                    slot_start = datetime.fromisoformat(slot['start_datetime'])
                    # Slot should not overlap with existing appointment
                    assert not (slot_start == conflict_time)
    
    @pytest.mark.asyncio
    async def test_list_slots_invalid_service(self):
        """Test that invalid service ID raises ValueError."""
        from tools.scheduler_tools import list_available_slots
        
        with patch('tools.scheduler_tools.get_service_by_id', return_value=None):
            with pytest.raises(ValueError, match="Service .* not found"):
                await list_available_slots(str(uuid4()))


class TestCreateBooking:
    """Tests for create_booking function with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_create_booking_validates_advance_time(self):
        """Test that booking validates minimum advance time."""
        from tools.scheduler_tools import create_booking
        
        # Try to book in 30 minutes (less than 1 hour minimum)
        start_time = datetime.now() + timedelta(minutes=30)
        
        with pytest.raises(ValueError, match="at least .* hour"):
            await create_booking(
                contact_id=str(uuid4()),
                service_id=str(uuid4()),
                start_datetime=start_time.isoformat()
            )
    
    @pytest.mark.asyncio
    async def test_create_booking_validates_business_hours(self):
        """Test that booking validates business hours."""
        from tools.scheduler_tools import create_booking
        
        # Try to book on Sunday (closed)
        # Find next Sunday
        today = date.today()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)
        start_time = datetime.combine(next_sunday, time(10, 0))
        
        with pytest.raises(ValueError, match="outside business hours"):
            await create_booking(
                contact_id=str(uuid4()),
                service_id=str(uuid4()),
                start_datetime=start_time.isoformat()
            )


class TestCancelBooking:
    """Tests for cancel_booking function with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_cancel_booking_within_policy(self):
        """Test cancellation within policy window."""
        from tools.reschedule_tools import cancel_booking
        
        # Mock appointment 48 hours in the future
        future_time = datetime.now() + timedelta(hours=48)
        
        mock_appointment = MagicMock()
        mock_appointment.id = uuid4()
        mock_appointment.service_id = uuid4()
        mock_appointment.start_ts = future_time
        mock_appointment.status = 'confirmed'
        
        mock_service = MagicMock()
        mock_service.id = mock_appointment.service_id
        mock_service.name = "Depilação a Laser"
        mock_service.category = "Depilação"
        
        mock_calendar = AsyncMock()
        mock_calendar.get_appointments = AsyncMock(return_value=[{
            'id': str(uuid4()),
            'appointment_date': future_time.date().isoformat(),
            'start_time': future_time.time().strftime('%H:%M'),
            'procedure': mock_service.name
        }])
        mock_calendar.delete_appointment = AsyncMock()
        
        with patch('tools.reschedule_tools.get_appointment_by_id', return_value=mock_appointment):
            with patch('tools.reschedule_tools.get_service_by_id', return_value=mock_service):
                with patch('tools.reschedule_tools.get_calendar_client', return_value=mock_calendar):
                    with patch('tools.reschedule_tools.update_appointment_status', new_callable=AsyncMock):
                        result = await cancel_booking(str(mock_appointment.id))
                        
                        assert result['success'] is True
                        assert result['policy_compliant'] is True
                        assert result['will_count_as_done'] is False
    
    @pytest.mark.asyncio
    async def test_cancel_booking_outside_policy(self):
        """Test cancellation outside policy window."""
        from tools.reschedule_tools import cancel_booking
        
        # Mock appointment 2 hours in the future (laser requires 24h)
        future_time = datetime.now() + timedelta(hours=2)
        
        mock_appointment = MagicMock()
        mock_appointment.id = uuid4()
        mock_appointment.service_id = uuid4()
        mock_appointment.start_ts = future_time
        mock_appointment.status = 'confirmed'
        
        mock_service = MagicMock()
        mock_service.id = mock_appointment.service_id
        mock_service.name = "Depilação a Laser"
        mock_service.category = "Depilação"
        
        with patch('tools.reschedule_tools.get_appointment_by_id', return_value=mock_appointment):
            with patch('tools.reschedule_tools.get_service_by_id', return_value=mock_service):
                with patch('tools.reschedule_tools.update_appointment_status', new_callable=AsyncMock):
                    result = await cancel_booking(str(mock_appointment.id))
                    
                    assert result['success'] is False
                    assert result['policy_compliant'] is False
                    assert result['will_count_as_done'] is True
                    assert 'prazo' in result['message'].lower()


class TestRescheduleBooking:
    """Tests for reschedule_booking function with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_reschedule_booking_exceeds_limit(self):
        """Test that rescheduling fails when limit is exceeded."""
        from tools.reschedule_tools import reschedule_booking
        
        # Mock appointment with 2 reschedules already
        future_time = datetime.now() + timedelta(hours=48)
        new_time = datetime.now() + timedelta(hours=72)
        
        mock_appointment = MagicMock()
        mock_appointment.id = uuid4()
        mock_appointment.service_id = uuid4()
        mock_appointment.start_ts = future_time
        mock_appointment.reschedule_count = 2  # Already at limit
        
        with patch('tools.reschedule_tools.get_appointment_by_id', return_value=mock_appointment):
            result = await reschedule_booking(
                str(mock_appointment.id),
                new_time.isoformat()
            )
            
            assert result['success'] is False
            assert result['reschedule_count'] == 2
            assert result['remaining_reschedules'] == 0
            assert 'limite' in result['message'].lower()
    
    @pytest.mark.asyncio
    async def test_reschedule_booking_validates_policy(self):
        """Test that rescheduling validates cancellation policy."""
        from tools.reschedule_tools import reschedule_booking
        
        # Mock appointment 2 hours in the future (laser requires 24h)
        future_time = datetime.now() + timedelta(hours=2)
        new_time = datetime.now() + timedelta(hours=48)
        
        mock_appointment = MagicMock()
        mock_appointment.id = uuid4()
        mock_appointment.service_id = uuid4()
        mock_appointment.start_ts = future_time
        mock_appointment.reschedule_count = 0
        
        mock_service = MagicMock()
        mock_service.id = mock_appointment.service_id
        mock_service.name = "Depilação a Laser"
        mock_service.category = "Depilação"
        
        with patch('tools.reschedule_tools.get_appointment_by_id', return_value=mock_appointment):
            with patch('tools.reschedule_tools.get_service_by_id', return_value=mock_service):
                result = await reschedule_booking(
                    str(mock_appointment.id),
                    new_time.isoformat()
                )
                
                assert result['success'] is False
                assert result['policy_compliant'] is False
                assert 'antecedência' in result['message'].lower()


# ============================================================================
# TIMEZONE TESTS
# ============================================================================

class TestTimezoneHandling:
    """Tests for timezone-aware datetime operations in reschedule tools."""
    
    @pytest.mark.asyncio
    async def test_cancel_booking_with_timezone_aware_appointment(self):
        """Test that cancel_booking handles timezone-aware appointments correctly."""
        from tools.reschedule_tools import cancel_booking
        
        # Create timezone-aware appointment (São Paulo timezone)
        sp_tz = ZoneInfo("America/Sao_Paulo")
        future_time = datetime.now(tz=sp_tz) + timedelta(hours=48)
        
        mock_appointment = MagicMock()
        mock_appointment.id = uuid4()
        mock_appointment.service_id = uuid4()
        mock_appointment.start_ts = future_time  # Timezone-aware
        mock_appointment.status = 'confirmed'
        
        mock_service = MagicMock()
        mock_service.id = mock_appointment.service_id
        mock_service.name = "Depilação a Laser"
        mock_service.category = "Depilação"
        
        mock_calendar = AsyncMock()
        mock_calendar.get_appointments = AsyncMock(return_value=[{
            'id': str(uuid4()),
            'appointment_date': future_time.date().isoformat(),
            'start_time': future_time.time().strftime('%H:%M'),
            'procedure': mock_service.name
        }])
        mock_calendar.delete_appointment = AsyncMock()
        
        with patch('tools.reschedule_tools.get_appointment_by_id', return_value=mock_appointment):
            with patch('tools.reschedule_tools.get_service_by_id', return_value=mock_service):
                with patch('tools.reschedule_tools.get_calendar_client', return_value=mock_calendar):
                    with patch('tools.reschedule_tools.update_appointment_status', new_callable=AsyncMock):
                        # Should not raise TypeError
                        result = await cancel_booking(str(mock_appointment.id))
                        
                        assert result['success'] is True
                        assert 'hours_before' in result
                        assert isinstance(result['hours_before'], (int, float))
    
    @pytest.mark.asyncio
    async def test_reschedule_booking_with_timezone_aware_appointment(self):
        """Test that reschedule_booking handles timezone-aware appointments correctly."""
        from tools.reschedule_tools import reschedule_booking
        
        # Create timezone-aware appointment (São Paulo timezone)
        # Use a fixed time during business hours (10:00 AM)
        sp_tz = ZoneInfo("America/Sao_Paulo")
        base_date = datetime.now(tz=sp_tz).replace(hour=10, minute=0, second=0, microsecond=0)
        future_time = base_date + timedelta(days=2)  # 2 days from now at 10 AM
        new_time = base_date + timedelta(days=3)  # 3 days from now at 10 AM
        
        mock_appointment = MagicMock()
        mock_appointment.id = uuid4()
        mock_appointment.service_id = uuid4()
        mock_appointment.start_ts = future_time  # Timezone-aware
        mock_appointment.reschedule_count = 0
        
        mock_service = MagicMock()
        mock_service.id = mock_appointment.service_id
        mock_service.name = "Depilação a Laser"
        mock_service.category = "Depilação"
        mock_service.duration_min = 60
        
        with patch('tools.reschedule_tools.get_appointment_by_id', return_value=mock_appointment):
            with patch('tools.reschedule_tools.get_service_by_id', return_value=mock_service):
                # Test should not raise TypeError during timezone calculation
                # We expect it to fail at calendar lookup (which is fine for this test)
                try:
                    result = await reschedule_booking(
                        str(mock_appointment.id),
                        new_time.isoformat()
                    )
                    # If it succeeds, check the result
                    assert 'hours_before' in result or result['success'] is True
                except ValueError as e:
                    # Expected to fail at calendar lookup, but should not be a TypeError
                    assert "Could not find calendar appointment" in str(e)
                    # The important part is that we got past the timezone calculation without TypeError
    
    @pytest.mark.asyncio
    async def test_check_cancellation_policy_with_timezone_aware_appointment(self):
        """Test that check_cancellation_policy handles timezone-aware appointments correctly."""
        from tools.reschedule_tools import check_cancellation_policy
        
        # Create timezone-aware appointment (São Paulo timezone)
        sp_tz = ZoneInfo("America/Sao_Paulo")
        future_time = datetime.now(tz=sp_tz) + timedelta(hours=48)
        
        mock_appointment = MagicMock()
        mock_appointment.id = uuid4()
        mock_appointment.service_id = uuid4()
        mock_appointment.contact_id = uuid4()
        mock_appointment.start_ts = future_time  # Timezone-aware
        
        mock_service = MagicMock()
        mock_service.id = mock_appointment.service_id
        mock_service.name = "Depilação a Laser"
        mock_service.category = "Depilação"
        
        mock_contact = MagicMock()
        mock_contact.no_show_count = 0
        
        with patch('tools.reschedule_tools.get_appointment_by_id', return_value=mock_appointment):
            with patch('tools.reschedule_tools.get_service_by_id', return_value=mock_service):
                with patch('models.repository.get_contact_by_id', new_callable=AsyncMock, return_value=mock_contact):
                    # Should not raise TypeError
                    result = await check_cancellation_policy(str(mock_appointment.id))
                    
                    assert 'hours_before' in result
                    assert isinstance(result['hours_before'], (int, float))
                    assert result['can_cancel'] is True  # 48h > 24h required


# ============================================================================
# KNOWLEDGE BASE TESTS
# ============================================================================

class TestKnowledgeBaseTools:
    """Tests for knowledge base tools to ensure consistent return types."""
    
    @pytest.mark.asyncio
    async def test_search_kb_with_empty_query_returns_dict(self):
        """Test that empty query returns dict with empty lists, not tuple."""
        from tools.kb_tools_cached import search_knowledge_base
        
        # Test with empty string
        result = await search_knowledge_base("")
        
        assert isinstance(result, dict), "Result should be a dict, not a tuple"
        assert "entries" in result
        assert "sources" in result
        assert result["entries"] == []
        assert result["sources"] == []
    
    @pytest.mark.asyncio
    async def test_search_kb_with_whitespace_query_returns_dict(self):
        """Test that whitespace-only query returns dict with empty lists."""
        from tools.kb_tools_cached import search_knowledge_base
        
        # Test with whitespace
        result = await search_knowledge_base("   ")
        
        assert isinstance(result, dict), "Result should be a dict, not a tuple"
        assert "entries" in result
        assert "sources" in result
        assert result["entries"] == []
        assert result["sources"] == []
    
    @pytest.mark.asyncio
    async def test_search_kb_with_valid_query_returns_dict(self):
        """Test that valid query returns dict with expected structure."""
        from tools.kb_tools_cached import search_knowledge_base
        
        mock_entries = [
            {"id": "1", "title": "Test Entry 1", "content": "Test content 1"},
            {"id": "2", "title": "Test Entry 2", "content": "Test content 2"}
        ]
        
        cache_service = MagicMock()
        cache_service.search_knowledge_base = AsyncMock(return_value=mock_entries)

        with patch(
            "tools.kb_tools_cached.get_kb_cache_service",
            return_value=cache_service,
        ):
            result = await search_knowledge_base("test query")
            
            assert isinstance(result, dict)
            assert "entries" in result
            assert "sources" in result
            assert len(result["entries"]) == 2
            assert len(result["sources"]) == 2
            assert result["sources"] == ["Test Entry 1", "Test Entry 2"]


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

class TestParseTime:
    """Tests for parse_time utility function."""
    
    def test_parse_time_valid(self):
        """Test parsing valid time strings."""
        assert parse_time("08:30") == time(8, 30)
        assert parse_time("19:00") == time(19, 0)
        assert parse_time("12:00") == time(12, 0)
    
    def test_parse_time_midnight(self):
        """Test parsing midnight."""
        assert parse_time("00:00") == time(0, 0)
    
    def test_parse_time_noon(self):
        """Test parsing noon."""
        assert parse_time("12:00") == time(12, 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
