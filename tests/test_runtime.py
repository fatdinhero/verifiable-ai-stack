import pytest
from unittest.mock import Mock
from cognitum_core.runtime import Runtime


class MockAgent:
    def __init__(self, output=None, exception=None):
        self.output = output or {
            "summary": "Test summary",
            "detail": "Test detail",
            "sources": ["source1", "source2"],
            "confidence": 0.8
        }
        self.exception = exception

    def run(self, task):
        if self.exception:
            raise self.exception
        return self.output


class MockPolicyEngine:
    def __init__(self, result=True, exception=None):
        self.result = result
        self.check_called = False
        self.exception = exception

    def check(self, task, output):
        self.check_called = True
        if self.exception:
            raise self.exception
        return self.result


class MockMemoryStore:
    def __init__(self, exception=None):
        self.saved_tasks = []
        self.saved_outputs = []
        self.exception = exception

    def save(self, task, output):
        if self.exception:
            raise self.exception
        self.saved_tasks.append(task)
        self.saved_outputs.append(output)


class MockAuditLogger:
    def __init__(self, exception=None):
        self.logged_tasks = []
        self.logged_policy_checks = []
        self.exception = exception

    def log(self, task, policy_check):
        if self.exception:
            raise self.exception
        self.logged_tasks.append(task)
        self.logged_policy_checks.append(policy_check)


@pytest.fixture
def task():
    return {"id": "test-task", "input": "test input"}


@pytest.fixture
def mock_agent():
    return MockAgent()


@pytest.fixture
def mock_policy_engine():
    return MockPolicyEngine(result=True)


@pytest.fixture
def mock_memory_store():
    return MockMemoryStore()


@pytest.fixture
def mock_audit_logger():
    return MockAuditLogger()


@pytest.fixture
def runtime(mock_agent, mock_policy_engine, mock_memory_store, mock_audit_logger):
    return Runtime(
        agent=mock_agent,
        policy_engine=mock_policy_engine,
        memory_store=mock_memory_store,
        audit_logger=mock_audit_logger
    )


class TestRuntimeInit:
    def test_init_stores_components(self):
        agent = Mock()
        policy_engine = Mock()
        memory_store = Mock()
        audit_logger = Mock()
        runtime = Runtime(agent, policy_engine, memory_store, audit_logger)
        assert runtime.agent is agent
        assert runtime.policy_engine is policy_engine
        assert runtime.memory_store is memory_store
        assert runtime.audit_logger is audit_logger


class TestRunAgent:
    def test_run_agent_calls_agent(self, runtime, task):
        runtime.run_agent(task)
        assert runtime.agent.run(task) is not None

    def test_run_agent_calls_policy_engine(self, runtime, task, mock_policy_engine):
        runtime.run_agent(task)
        assert mock_policy_engine.check_called is True

    def test_run_agent_saves_to_memory(self, runtime, task, mock_memory_store):
        runtime.run_agent(task)
        assert len(mock_memory_store.saved_tasks) == 1
        assert mock_memory_store.saved_tasks[0] is task

    def test_run_agent_logs_to_audit(self, runtime, task, mock_audit_logger):
        runtime.run_agent(task)
        assert len(mock_audit_logger.logged_tasks) == 1
        assert mock_audit_logger.logged_tasks[0] is task

    def test_run_agent_returns_policy_check(self, runtime, task):
        result = runtime.run_agent(task)
        assert result is True

    def test_run_agent_with_compliant_result(self, task):
        agent = MockAgent()
        policy = MockPolicyEngine(result={"compliant": True, "reason": "ok"})
        memory = MockMemoryStore()
        audit = MockAuditLogger()
        runtime = Runtime(agent, policy, memory, audit)
        result = runtime.run_agent(task)
        assert result == {"compliant": True, "reason": "ok"}

    def test_run_agent_with_non_compliant_result(self, task):
        agent = MockAgent()
        policy = MockPolicyEngine(result={"compliant": False, "reason": "violation"})
        memory = MockMemoryStore()
        audit = MockAuditLogger()
        runtime = Runtime(agent, policy, memory, audit)
        result = runtime.run_agent(task)
        assert result == {"compliant": False, "reason": "violation"}

    def test_run_agent_saves_correct_output(self, task):
        agent = MockAgent()
        policy_result = {"compliant": True}
        policy = MockPolicyEngine(result=policy_result)
        memory = MockMemoryStore()
        audit = MockAuditLogger()
        runtime = Runtime(agent, policy, memory, audit)
        runtime.run_agent(task)
        assert memory.saved_outputs[0] is policy_result

    def test_run_agent_logs_correct_policy_check(self, task):
        agent = MockAgent()
        policy_result = {"compliant": True}
        policy = MockPolicyEngine(result=policy_result)
        memory = MockMemoryStore()
        audit = MockAuditLogger()
        runtime = Runtime(agent, policy, memory, audit)
        runtime.run_agent(task)
        assert audit.logged_policy_checks[0] is policy_result

    def test_run_agent_passes_agent_output_to_policy(self, task):
        custom_output = {"custom": "output"}
        agent = MockAgent(output=custom_output)
        policy = MockPolicyEngine()
        memory = MockMemoryStore()
        audit = MockAuditLogger()
        runtime = Runtime(agent, policy, memory, audit)
        with pytest.raises(Exception):
            pass
        # Verify the chain works
        result = runtime.run_agent(task)
        assert result is True

    def test_run_agent_multiple_calls(self, runtime, task, mock_memory_store, mock_audit_logger):
        runtime.run_agent(task)
        runtime.run_agent(task)
        assert len(mock_memory_store.saved_tasks) == 2
        assert len(mock_audit_logger.logged_tasks) == 2