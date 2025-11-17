# Testing Guide - Virtual Travel Assistant

Comprehensive testing covering Lambda handler and AgentCore runtime with Unit, Adversarial, Performance, and Load tests.

## 🚀 Quick Start

```bash
# Run all tests
./tests/run_tests.sh
```

## 📊 Test Suite

**42 comprehensive tests** covering all components:

### Lambda Handler Tests (17 tests)

#### 1. Unit Tests (6 tests)
Individual component testing:
- ✅ Health check endpoint
- ✅ CORS preflight handling
- ✅ Simple message handling
- ✅ Missing message error handling
- ✅ Session ID propagation
- ✅ Thinking tags removal

#### 2. Adversarial Tests (5 tests)
Security and robustness:
- ✅ Prompt injection resistance
- ✅ SQL injection handling
- ✅ Special characters handling
- ✅ Extremely long input handling
- ✅ Malformed JSON handling

#### 3. Performance Tests (3 tests)
Speed and efficiency:
- ✅ Health check latency (< 1s)
- ✅ Simple request latency (< 5s)
- ✅ Multiple sequential requests

#### 4. Load Tests (3 tests)
Concurrent request handling:
- ✅ Concurrent different sessions (10 concurrent)
- ✅ Burst traffic (20 simultaneous)
- ✅ Sustained load (30 requests, 95% success)

### AgentCore Runtime Tests (25 tests)

#### Configuration Tests (4 tests)
- ✅ Environment variables loaded
- ✅ Memory ID configured
- ✅ Region configured
- ✅ Model ID configured

#### Agent Structure Tests (3 tests)
- ✅ Session agents dictionary
- ✅ Memory client initialized
- ✅ App initialized

#### Search Tool Tests (3 tests)
- ✅ search_web function exists
- ✅ search_web is callable
- ✅ Tavily client configured

#### Agent Creation Tests (2 tests)
- ✅ get_or_create_agent exists
- ✅ get_or_create_agent documented

#### Entrypoint Tests (2 tests)
- ✅ travel_agent_entrypoint exists
- ✅ travel_agent_entrypoint callable

#### Additional Tests (11 tests)
- System prompt configuration
- Payload handling (input, session_id, action)
- Memory configuration
- Guardrail configuration
- Module structure

## 📈 Current Coverage

- **42/42 tests passing** ✅
- **Lambda Handler**: 52% coverage
- **AgentCore Runtime**: 30% coverage
- **Overall**: 40% coverage
- **< 1 second** execution time

## 🔧 Running Tests

### Run All Tests
```bash
./tests/run_tests.sh
```

### Run Specific Test File
```bash
# Lambda handler tests only
pytest tests/test_basic.py -v

# AgentCore runtime tests only
pytest tests/test_agent_runtime.py -v
```

### Run Specific Test Type
```bash
# Unit tests only
pytest tests/test_basic.py::TestUnitTests -v

# Adversarial tests only
pytest tests/test_basic.py::TestAdversarialTests -v

# Performance tests only
pytest tests/test_basic.py::TestPerformanceTests -v

# Load tests only
pytest tests/test_basic.py::TestLoadTests -v

# Configuration tests only
pytest tests/test_agent_runtime.py::TestConfiguration -v
```

### View Coverage Report
```bash
open htmlcov/index.html
```

## 📝 Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_basic.py            # 17 Lambda handler tests
│   ├── TestUnitTests           (6 tests)
│   ├── TestAdversarialTests    (5 tests)
│   ├── TestPerformanceTests    (3 tests)
│   └── TestLoadTests           (3 tests)
├── test_agent_runtime.py    # 25 AgentCore runtime tests
│   ├── TestConfiguration       (4 tests)
│   ├── TestAgentStructure      (3 tests)
│   ├── TestSearchToolStructure (3 tests)
│   └── ... (7 more test classes)
├── run_tests.sh             # Test runner
└── requirements.txt         # Dependencies
```

## ✅ Success Criteria

All tests pass:
```
============================== 42 passed in 0.22s ==============================
✓ All tests passed!
```

## 🎯 Test Methodology

### Unit Tests
Test individual components in isolation with mocked dependencies.

### Adversarial Tests
Test security by attempting:
- Prompt injection attacks
- SQL injection patterns
- Special character exploits
- Resource exhaustion (long inputs)
- Malformed data

### Performance Tests
Measure response times and ensure:
- Health checks < 1s
- Simple requests < 5s
- No performance degradation

### Load Tests
Test concurrent request handling:
- Multiple simultaneous sessions
- Burst traffic scenarios
- Sustained load with high success rate

### Configuration Tests
Verify proper setup:
- Environment variables
- Memory configuration
- Model configuration
- Guardrail configuration

### Structure Tests
Verify code organization:
- Required functions exist
- Proper module structure
- Correct imports

## 🐛 Troubleshooting

### Import Errors
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Tests Not Running
```bash
chmod +x tests/run_tests.sh
```

## 📚 Adding New Tests

### For Lambda Handler
Add to `tests/test_basic.py`:

```python
class TestUnitTests:
    @patch('handler.agent_core_client')
    def test_my_feature(self, mock_client, sample_lambda_event, sample_lambda_context, env_vars):
        """Test description."""
        mock_response = Mock()
        mock_response.read = Mock(return_value=b'Expected response')
        mock_client.invoke_agent_runtime.return_value = {
            'response': mock_response
        }
        
        response = handler.lambda_handler(sample_lambda_event, sample_lambda_context)
        assert response['statusCode'] == 200
```

### For AgentCore Runtime
Add to `tests/test_agent_runtime.py`:

```python
class TestNewFeature:
    def test_feature_exists(self):
        """Test that feature exists."""
        import runtime_agent_main
        
        assert hasattr(runtime_agent_main, 'feature_name')
        assert callable(runtime_agent_main.feature_name)
```

## 🎓 Philosophy

We focus on:
- **Comprehensive** - All test types covered (unit, adversarial, performance, load, configuration, structure)
- **Complete** - Tests both Lambda and AgentCore components
- **Fast** - All tests run in < 1 second
- **Maintainable** - Clear organization by component and test type
- **Practical** - Tests real-world scenarios

## 📊 Test Distribution

```
Lambda Handler Tests:    ████████████████████████████ 40% (17 tests)
AgentCore Runtime Tests: ████████████████████████████████████ 60% (25 tests)
```

---

**Ready to test?**

```bash
./tests/run_tests.sh
```
