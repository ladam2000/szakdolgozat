# Testing Guide - Virtual Travel Assistant

Comprehensive testing covering Unit, Adversarial, Performance, and Load tests.

## 🚀 Quick Start

```bash
# Run all tests
./tests/run_tests.sh
```

## 📊 Test Suite

**17 comprehensive tests** covering all essential testing types:

### 1. Unit Tests (6 tests)
Individual component testing:
- ✅ Health check endpoint
- ✅ CORS preflight handling
- ✅ Simple message handling
- ✅ Missing message error handling
- ✅ Session ID propagation
- ✅ Thinking tags removal

### 2. Adversarial Tests (5 tests)
Security and robustness testing:
- ✅ Prompt injection resistance
- ✅ SQL injection handling
- ✅ Special characters handling
- ✅ Extremely long input handling
- ✅ Malformed JSON handling

### 3. Performance Tests (3 tests)
Speed and efficiency testing:
- ✅ Health check latency (< 1s)
- ✅ Simple request latency (< 5s)
- ✅ Multiple sequential requests

### 4. Load Tests (3 tests)
Concurrent request handling:
- ✅ Concurrent different sessions (10 concurrent)
- ✅ Burst traffic (20 simultaneous)
- ✅ Sustained load (30 requests, 95% success)

## 📈 Current Coverage

- **17/17 tests passing** ✅
- **50% code coverage** on lambda/handler.py
- **< 1 second** execution time

## 🔧 Running Tests

### Run All Tests
```bash
./tests/run_tests.sh
```

## 📝 Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_basic.py        # 17 comprehensive tests
│   ├── TestUnitTests           (6 tests)
│   ├── TestAdversarialTests    (5 tests)
│   ├── TestPerformanceTests    (3 tests)
│   └── TestLoadTests           (3 tests)
├── run_tests.sh         # Test runner
└── requirements.txt     # Dependencies
```

## ✅ Success Criteria

All tests pass:
```
============================== 17 passed in 0.49s ==============================
✓ All tests passed!
```



## 🐛 Troubleshooting

### Import Errors
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Tests Not Running
```bash
chmod +x tests/run_tests.sh
```


