from typing import Dict, Any, Optional

class Runtime:
    """Orchestrates the execution pipeline: Agent → PolicyEngine → MemoryStore → AuditLogger.
    
    Coordinates multiple components to process tasks while ensuring policy compliance,
    memory persistence, and audit trail generation.
    """
    
    def __init__(
        self,
        agent: Any,
        policy_engine: Any,
        memory_store: Any,
        audit_logger: Any
    ) -> None:
        """Initialize runtime with all required components.
        
        Args:
            agent: Agent instance capable of processing tasks
            policy_engine: Engine to validate outputs against policies
            memory_store: Storage system for persistence
            audit_logger: Logger for audit trail
        """
        self.agent = agent
        self.policy_engine = policy_engine
        self.memory_store = memory_store
        self.audit_logger = audit_logger
    
    def run_agent(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full pipeline for a given task.
        
        Pipeline order:
        1. Agent processes the task
        2. Policy engine validates the output
        3. If valid, memory store persists the result
        4. Audit logger records the action
        5. Return the final output
        
        Args:
            task: Dictionary containing task parameters and context
            
        Returns:
            Dictionary following schema: {summary, detail, sources, confidence}
            
        Raises:
            ValueError: If policy validation fails
        """
        # Step 1: Agent processes the task
        raw_output = self.agent.run(task)
        
        # Step 2: Policy engine validates output
        policy_check = self.policy_engine.check(raw_output)
        
        if not policy_check:
            raise ValueError("Output failed policy validation")
        
        # Step 3: Memory store persists the result
        self.memory_store.save(raw_output)
        
        # Step 4: Audit logger records the action
        self.audit_logger.log({
            "task": task,
            "output": raw_output,
            "timestamp": self._get_current_timestamp()
        })
        
        # Step 5: Ensure output follows required schema
        return self._format_output(raw_output)
    
    def _format_output(self, raw_output: Any) -> Dict[str, Any]:
        """Ensure output matches required schema.
        
        Args:
            raw_output: Raw output from agent
            
        Returns:
            Dictionary with required fields: summary, detail, sources, confidence
            
        Raises:
            ValueError: If output cannot be formatted to required schema
        """
        if isinstance(raw_output, dict):
            # Ensure all required fields exist
            formatted = {
                "summary": raw_output.get("summary", ""),
                "detail": raw_output.get("detail", ""),
                "sources": raw_output.get("sources", []),
                "confidence": raw_output.get("confidence", 0.0)
            }
            
            # Validate confidence is between 0 and 1
            if not (0.0 <= formatted["confidence"] <= 1.0):
                formatted["confidence"] = max(0.0, min(1.0, formatted["confidence"]))
            
            return formatted
        
        # If output is not a dict, wrap it in the required schema
        return {
            "summary": str(raw_output),
            "detail": "",
            "sources": [],
            "confidence": 0.5  # Default medium confidence for non-standard output
        }
    
    @staticmethod
    def _get_current_timestamp() -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            Current timestamp string in ISO 8601 format
        """
        from datetime import datetime
        return datetime.now().isoformat()