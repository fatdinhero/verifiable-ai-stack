import pytest
from unittest.mock import Mock, MagicMock, patch
from cognitum_core.runtime import Runtime

@pytest.fixture
def mock_components():
    agent = Mock()
    policy_engine = Mock()
    memory_store = Mock()
    audit_logger = Mock()
    return agent, policy_engine, memory_store, audit_logger

@pytest.fixture
def runtime(mock_components):
    agent, policy_engine, memory_store, audit_logger = mock_components
    return Runtime(agent, policy_engine, memory_store, audit_logger)

def test_runtime_initialization(mock_components):
    agent, policy_engine, memory_store, audit_logger = mock_components
    runtime = Runtime(agent, policy_engine, memory_store, audit_logger)
    assert runtime.agent is agent
    assert runtime.policy_engine is policy_engine
    assert runtime.memory_store is memory_store
    assert runtime.audit_logger is audit_logger

def test_run_agent_success(runtime, mock_components):
    agent, policy_engine, memory_store, audit_logger = mock_components
    task = {"input": "test task"}
    agent_output = {"summary": "test summary", "detail": "test detail", "sources": ["source1"], "confidence": 0.9}
    agent.run.return_value = agent_output
    policy_engine.check.return_value = True

    result = runtime.run_agent(task)

    agent.run.assert_called_once_with(task)
    policy_engine.check.assert_called_once_with(agent_output)
    memory_store.save.assert_called_once_with(agent_output)
    audit_logger.log.assert_called_once()
    log_data = audit_logger.log.call_args[0][0]
    assert log_data["task"] == task
    assert log_data["output"] == agent_output
    assert "timestamp" in log_data
    assert result == agent_output

def test_run_agent_policy_failure(runtime, mock_components):
    agent, policy_engine, memory_store, audit_logger = mock_components
    task = {"input": "test task"}
    agent_output = {"summary": "test", "confidence": 0.8}
    agent.run.return_value = agent_output
    policy_engine.check.return_value = False

    with pytest.raises(ValueError, match="Output failed policy validation"):
        runtime.run_agent(task)

    agent.run.assert_called_once_with(task)
    policy_engine.check.assert_called_once_with(agent_output)
    memory_store.save.assert_not_called()
    audit_logger.log.assert_not_called()

def test_format_output_with_dict(runtime):
    raw = {"summary": "sum", "detail": "det", "sources": ["s1"], "confidence": 0.8}
    result = runtime._format_output(raw)
    assert result == raw

def test_format_output_dict_missing_fields(runtime):
    raw = {"summary": "sum"}
    result = runtime._format_output(raw)
    expected = {
        "summary": "sum",
        "detail": "",
        "sources": [],
        "confidence": 0.0
    }
    assert result == expected

def test_format_output_dict_high_confidence(runtime):
    raw = {"summary": "sum", "detail": "det", "sources": [], "confidence": 1.5}
    result = runtime._format_output(raw)
    assert result["confidence"] == 1.0

def test_format_output_dict_low_confidence(runtime):
    raw = {"summary": "sum", "detail": "det", "sources": [], "confidence": -0.2}
    result = runtime._format_output(raw)
    assert result["confidence"] == 0.0

def test_format_output_non_dict(runtime):
    raw = "string output"
    result = runtime._format_output(raw)
    expected = {
        "summary": "string output",
        "detail": "",
        "sources": [],
        "confidence": 0.5
    }
    assert result == expected

def test_get_current_timestamp_format():
    timestamp = Runtime._get_current_timestamp()
    assert isinstance(timestamp, str)
    assert "T" in timestamp

@patch('cognitum_core.runtime.datetime')
def test_get_current_timestamp_mocked(mock_datetime):
    mock_now = Mock()
    mock_now.isoformat.return_value = "2024-01-01T00:00:00"
    mock_datetime.now.return_value = mock_now
    
    timestamp = Runtime._get_current_timestamp()
    mock_datetime.now.assert_called_once()
    mock_now.isoformat.assert_called_once()
    assert timestamp == "2024-01-01T00:00:00"

def test_run_agent_output_formatting(runtime, mock_components):
    agent, policy_engine, memory_store, audit_logger = mock_components
    task = {"input": "test"}
    raw_output = {"confidence": 2.0, "summary": "s"}
    agent.run.return_value = raw_output
    policy_engine.check.return_value = True

    result = runtime.run_agent(task)

    assert result["confidence"] == 1.0
    assert result["detail"] == ""
    assert result["sources"] == []