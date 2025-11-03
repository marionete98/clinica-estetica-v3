# Integration Tests - Quick Start Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# Required: MODEL_PROVIDER, GEMINI_API_KEY (or XAI_API_KEY), 
#           SUPABASE_URL, SUPABASE_KEY, REDIS_URL
```

### 3. Run All Tests

```bash
# Using the test runner (recommended)
python tests/run_integration_tests.py

# Or using pytest directly
pytest tests/test_e2e.py tests/test_performance.py tests/test_error_scenarios.py -v
```

## 📋 Test Suites

### End-to-End Tests (24 scenarios)
```bash
pytest tests/test_e2e.py -v
```
Tests complete conversation flows: FAQ, scheduling, rescheduling

### Performance Tests
```bash
pytest tests/test_performance.py -v
```
Validates P95 latency ≤ 7 seconds and webhook acceptance < 1s

### Error Scenario Tests
```bash
pytest tests/test_error_scenarios.py -v
```
Tests graceful degradation when Redis, Supabase, or LLM fail

## 🎯 Run Specific Tests

```bash
# Run only FAQ tests
pytest tests/test_e2e.py -k "faq" -v

# Run only scheduling tests
pytest tests/test_e2e.py -k "schedule" -v

# Run a specific test
pytest tests/test_e2e.py::test_faq_treatment_information -v
```

## 📊 Generate Coverage Report

```bash
pytest tests/ --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## ✅ Success Criteria

- ✓ 0 errors (5xx) across all 24 conversations
- ✓ Webhook acceptance < 1 second
- ✓ P95 latency ≤ 7 seconds
- ✓ System operates when Redis is down
- ✓ System continues when Supabase is slow
- ✓ System handles LLM timeouts

## 🔧 Troubleshooting

### Connection Errors
```bash
# Check environment variables
cat .env

# Verify services are running
redis-cli ping  # Should return PONG
```

### Test Data Cleanup
```bash
# Clean up test data
pytest tests/test_e2e.py::test_cleanup_test_data -v
```

### Rate Limits
If you hit LLM API rate limits, add delays:
```python
await asyncio.sleep(1.0)  # Between tests
```

## 📚 Full Documentation

See `tests/README_INTEGRATION_TESTS.md` for complete documentation.

## 🎉 Expected Output

```
================================ test session starts =================================
tests/test_e2e.py::test_faq_treatment_information PASSED                      [  4%]
tests/test_e2e.py::test_faq_pricing_fixed PASSED                              [  8%]
...
tests/test_performance.py::test_webhook_acceptance_latency PASSED             [ 92%]
tests/test_error_scenarios.py::test_redis_unavailable_graceful_degradation PASSED [ 96%]
...

================================ 30 passed in 45.2s =================================
```

## 💡 Tips

- Run tests in order: E2E → Performance → Error Scenarios
- Use `-v` flag for verbose output
- Use `-s` flag to see print statements
- Use `--tb=short` for shorter tracebacks
- Tests create unique IDs to avoid conflicts
- Test data is automatically cleaned up

## 🚨 Common Issues

**Issue:** `python` command not found  
**Solution:** Use `python3` or install Python 3.13.1+

**Issue:** Tests fail with connection errors  
**Solution:** Check `.env` file and verify services are accessible

**Issue:** Tests are slow  
**Solution:** Normal - tests include wait times for background processing

**Issue:** Some tests skip  
**Solution:** Expected if optional dependencies are missing

## 📞 Need Help?

- Check `tests/README_INTEGRATION_TESTS.md` for detailed docs
- Review `docs/TASK_15_INTEGRATION_TESTS_SUMMARY.md` for implementation details
- See `docs/ERROR_HANDLING_GUIDE.md` for error handling info
