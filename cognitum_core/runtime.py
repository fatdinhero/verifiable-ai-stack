class Runtime:
    def __init__(self, agent, policy_engine, memory_store, audit_logger):
        self.agent = agent
        self.policy_engine = policy_engine
        self.memory_store = memory_store
        self.audit_logger = audit_logger

    def run_agent(self, task: dict) -> dict:
        agent_output = self.agent.run(task)
        policy_check = self.policy_engine.check(task, agent_output)
        self.memory_store.save(task, policy_check)
        self.audit_logger.log(task, policy_check)
        return policy_check