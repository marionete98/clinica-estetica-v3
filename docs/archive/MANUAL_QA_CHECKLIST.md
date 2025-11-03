# Manual QA Testing Checklist

Quick reference checklist for executing manual QA tests on the Clínica Luana Multi-Agent System.

## Pre-Test Setup

- [ ] System is running and healthy (`GET /health` returns 200)
- [ ] WhatsApp access configured
- [ ] Chatwoot admin access available
- [ ] Supabase read access available
- [ ] Test phone numbers prepared
- [ ] Knowledge base populated
- [ ] Previous test data cleared (if needed)

## FAQ Tests (8 scenarios)

### FAQ-01: Treatment Information
- [ ] Send: "Olá! Gostaria de saber sobre depilação a laser"
- [ ] ✓ Response contains treatment information
- [ ] ✓ Professional and welcoming tone
- [ ] ✓ No incorrect information

### FAQ-02: Fixed Pricing
- [ ] Send: "Quanto custa a depilação a laser?"
- [ ] ✓ Price information provided or consultation mentioned
- [ ] ✓ Clear and accurate

### FAQ-03: Consultation Pricing
- [ ] Send: "Quanto custa harmonização facial?"
- [ ] ✓ Mentions consultation requirement
- [ ] ✓ States consultation price (R$200)
- [ ] ✓ Explains abatement policy

### FAQ-04: Cancellation Policy
- [ ] Send: "Qual é a política de cancelamento?"
- [ ] ✓ Explains policies correctly
- [ ] ✓ Differentiates by treatment type
- [ ] ✓ 4h for harmonização, 24h for laser

### FAQ-05: Contraindications
- [ ] Send: "Quais são as contraindicações para depilação a laser?"
- [ ] ✓ Lists contraindications
- [ ] ✓ Recommends consultation if needed
- [ ] ✓ Professional tone

### FAQ-06: Post-Treatment Care
- [ ] Send: "Quais cuidados devo ter após a depilação a laser?"
- [ ] ✓ Provides care instructions
- [ ] ✓ Mentions sun avoidance, SPF, hydration
- [ ] ✓ Practical and clear

### FAQ-07: Business Hours
- [ ] Send: "Qual é o horário de funcionamento da clínica?"
- [ ] ✓ Mon-Fri 08:30-19:00
- [ ] ✓ Sat 08:30-12:00
- [ ] ✓ Sun closed

### FAQ-08: Escalation
- [ ] Send: "Preciso falar com um atendente humano"
- [ ] ✓ Recognizes escalation request
- [ ] ✓ Conversation assigned in Chatwoot
- [ ] ✓ Handoff message sent
- [ ] ✓ Automation paused

## Scheduling Tests (8 scenarios)

### SCH-01: Simple Booking
- [ ] Send: "Olá, gostaria de agendar depilação a laser para amanhã"
- [ ] ✓ Collects name if needed
- [ ] ✓ Shows available slots (≥3 options)
- [ ] ✓ Requests explicit confirmation
- [ ] ✓ Creates booking in database
- [ ] ✓ Sends confirmation message

### SCH-02: No Available Slots
- [ ] Send: "Quero agendar para hoje às 20:00"
- [ ] ✓ Explains unavailability
- [ ] ✓ Mentions business hours
- [ ] ✓ Suggests alternatives

### SCH-03: Outside Business Hours
- [ ] Send: "Posso agendar para domingo?"
- [ ] ✓ Explains clinic closed on Sundays
- [ ] ✓ States business hours
- [ ] ✓ Suggests valid days

### SCH-04: Insufficient Advance
- [ ] Send: "Quero agendar para daqui 30 minutos"
- [ ] ✓ Explains 1-hour minimum
- [ ] ✓ Clear policy explanation
- [ ] ✓ Suggests valid times

### SCH-05: Confirmation Flow
- [ ] Send: "Quero agendar harmonização facial"
- [ ] ✓ Shows available slots
- [ ] ✓ Requests confirmation
- [ ] ✓ Only creates after confirmation
- [ ] ✓ Confirmation has all details

### SCH-06: Check Existing Bookings
- [ ] Send: "Quais são meus agendamentos?"
- [ ] ✓ Lists future bookings
- [ ] ✓ Shows date, time, procedure
- [ ] ✓ Clear format

### SCH-07: Multiple Services
- [ ] Send: "Posso agendar depilação e harmonização no mesmo dia?"
- [ ] ✓ Explains possibility/limitations
- [ ] ✓ Considers duration
- [ ] ✓ Practical suggestions

### SCH-08: Consultation Booking
- [ ] Send: "Quero agendar uma consulta para harmonização"
- [ ] ✓ Recognizes consultation need
- [ ] ✓ States consultation price
- [ ] ✓ Explains abatement
- [ ] ✓ Offers booking

## Rescheduling/Cancellation Tests (8 scenarios)

### RES-01: Valid Cancellation
- [ ] Send: "Preciso cancelar meu agendamento de amanhã"
- [ ] ✓ Finds booking
- [ ] ✓ Validates policy (4h/24h)
- [ ] ✓ Confirms cancellation
- [ ] ✓ Updates status to 'cancelled'
- [ ] ✓ Sends confirmation

### RES-02: Invalid Cancellation
- [ ] Send: "Preciso cancelar meu agendamento de hoje (2h antes)"
- [ ] ✓ Validates policy
- [ ] ✓ Explains outside timeframe
- [ ] ✓ Mentions session will be counted
- [ ] ✓ Offers escalation

### RES-03: First Rescheduling
- [ ] Send: "Gostaria de remarcar meu agendamento para outro dia"
- [ ] ✓ Finds booking
- [ ] ✓ Checks counter (should be 0)
- [ ] ✓ Shows available slots
- [ ] ✓ Allows rescheduling
- [ ] ✓ Increments counter to 1

### RES-04: Second Rescheduling
- [ ] Send: "Preciso remarcar novamente meu agendamento"
- [ ] ✓ Checks counter (should be 1)
- [ ] ✓ Allows second rescheduling
- [ ] ✓ Warns about limit
- [ ] ✓ Increments counter to 2

### RES-05: Third Attempt (Blocked)
- [ ] Send: "Preciso remarcar pela terceira vez"
- [ ] ✓ Checks counter (should be 2)
- [ ] ✓ Blocks rescheduling
- [ ] ✓ Explains 2-reschedule limit
- [ ] ✓ Offers escalation

### RES-06: Non-Existent Booking
- [ ] Send: "Quero cancelar meu agendamento"
- [ ] ✓ Searches for bookings
- [ ] ✓ Informs no active bookings
- [ ] ✓ Offers to schedule new

### RES-07: Unavailable Slot
- [ ] Send: "Quero remarcar para domingo às 15:00"
- [ ] ✓ Validates requested time
- [ ] ✓ Explains unavailability
- [ ] ✓ States business hours
- [ ] ✓ Suggests alternatives

### RES-08: No-Show Policy
- [ ] Send: "O que acontece se eu não comparecer?"
- [ ] ✓ Explains no-show policy
- [ ] ✓ Mentions session counted as done
- [ ] ✓ Clear consequences
- [ ] ✓ Educational tone

## Post-Test Validation

### Database Verification
- [ ] Check appointments table for new bookings
- [ ] Verify status updates (cancelled, confirmed)
- [ ] Check reschedule_count increments
- [ ] Verify contact records created/updated

### Logs Verification
- [ ] Query logs table for test conversations
- [ ] Check for 5xx errors (should be 0)
- [ ] Verify intents logged correctly
- [ ] Check latency values

### Metrics Calculation
- [ ] Calculate P95 latency from results
- [ ] Verify P95 ≤ 7 seconds
- [ ] Count total bookings created
- [ ] Verify 100% message delivery

## Success Criteria (Requirements 11.1-11.5)

- [ ] **11.1**: 0 errors (5xx) across all 24 conversations
- [ ] **11.2**: 100% of scheduling tests created bookings
- [ ] **11.3**: All rescheduling/cancellation tests updated status correctly
- [ ] **11.4**: P95 latency ≤ 7 seconds
- [ ] **11.5**: All messages delivered via WhatsApp

## Final Report

- [ ] All 24 tests executed
- [ ] Results documented
- [ ] Pass/fail counts recorded
- [ ] Issues documented with details
- [ ] Recommendations provided
- [ ] Results saved to file

## Sign-Off

**Tester**: ___________________________  
**Date**: ___________________________  
**Environment**: ___________________________  
**Overall Result**: ⬜ PASS  ⬜ FAIL  
**Notes**: ___________________________

---

**Quick Commands**:
```bash
# Run interactive test guide
python scripts/manual_qa_test_guide.py

# Run specific category
python scripts/manual_qa_test_guide.py --category faq
python scripts/manual_qa_test_guide.py --category scheduling
python scripts/manual_qa_test_guide.py --category rescheduling

# Check system health
curl http://localhost:8000/health

# View recent logs
python -c "from config.supabase_client import supabase_client; print(supabase_client.client.table('logs').select('*').order('ts', desc=True).limit(10).execute())"
```
