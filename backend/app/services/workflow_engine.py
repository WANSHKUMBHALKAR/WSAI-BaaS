import asyncio
import logging
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.workflow import Workflow, WorkflowRun
from app.services.ai_gateway.gateway import AIGateway
from app.services.ai_gateway.base import ChatMessage
from app.agents.runtime import AgentRuntime

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """
    Executes a visual-builder-defined workflow graph.
    Nodes can represent LLM queries, Agent tasks, Webhooks, or Conditional branches.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.gateway = AIGateway(db=db)

    async def execute_run(self, workflow_id: uuid.UUID, input_data: Dict[str, Any]) -> WorkflowRun:
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow with ID {workflow_id} not found")

        # Create new execution run
        run = WorkflowRun(
            workflow_id=workflow_id,
            status="running",
            input_data=input_data,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        try:
            definition = workflow.definition
            nodes = definition.get("nodes", [])
            edges = definition.get("edges", [])

            # Simple execution queue (topological sort or linear path traversal)
            # For demonstration, we execute nodes based on dependecy order
            # Let's map nodes by ID
            node_map = {node["id"]: node for node in nodes}
            
            # Simple state dictionary tracking intermediate results
            execution_state = {"input": input_data}

            # Find root nodes (no incoming edges)
            target_ids = {edge["target"] for edge in edges}
            current_nodes = [node for node in nodes if node["id"] not in target_ids]

            visited = set()
            while current_nodes:
                next_nodes = []
                for node in current_nodes:
                    if node["id"] in visited:
                        continue
                    
                    node_id = node["id"]
                    node_type = node.get("type")
                    node_data = node.get("data", {})

                    logger.info("Executing node %s of type %s", node_id, node_type)

                    # Execute the node
                    node_output = await self._execute_node(node_type, node_data, execution_state)
                    execution_state[node_id] = node_output

                    visited.add(node_id)

                    # Find downstream children
                    children = [node_map[edge["target"]] for edge in edges if edge["source"] == node_id]
                    for child in children:
                        # Ensure all parents of this child are visited (simple topological execution check)
                        parents = [edge["source"] for edge in edges if edge["target"] == child["id"]]
                        if all(p in visited for p in parents):
                            next_nodes.append(child)

                current_nodes = next_nodes

            run.status = "completed"
            run.output_data = execution_state
            run.completed_at = datetime.now(timezone.utc)
        except Exception as exc:
            logger.error("Workflow run %s failed: %s", run.id, exc, exc_info=True)
            run.status = "failed"
            run.error = str(exc)
            run.completed_at = datetime.now(timezone.utc)
        
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    async def _execute_node(self, node_type: str, node_data: Dict[str, Any], state: Dict[str, Any]) -> Any:
        if node_type == "llm":
            prompt = node_data.get("prompt", "")
            # Interpolate variables from execution state
            formatted_prompt = self._interpolate(prompt, state)
            messages = [ChatMessage(role="user", content=formatted_prompt)]
            model = node_data.get("model", "gpt-4o-mini")
            response = await self.gateway.chat(messages=messages, model=model)
            return {"text": response.content, "tokens": response.total_tokens}

        elif node_type == "agent":
            agent_id = node_data.get("agent_id")
            user_input = node_data.get("input", "")
            formatted_input = self._interpolate(user_input, state)
            if not agent_id:
                raise ValueError("Agent Node requires an agent_id")
            
            runtime = AgentRuntime(
                agent_id=str(agent_id),
                user_id="workflow-engine-user",
                model=node_data.get("model", "gpt-4o")
            )
            result = await runtime.run(formatted_input)
            return result

        elif node_type == "condition":
            # Simple condition check
            field = node_data.get("field", "")
            value = node_data.get("value", "")
            operator = node_data.get("operator", "equals")
            
            resolved_value = self._get_nested_value(state, field)
            
            if operator == "equals":
                return resolved_value == value
            elif operator == "contains":
                return value in str(resolved_value)
            return False

        elif node_type == "placeholder":
            return {"status": "skipped"}

        else:
            raise ValueError(f"Unknown node type: {node_type}")

    def _interpolate(self, text: str, state: Dict[str, Any]) -> str:
        # Simple template string replacement, e.g. {{input.question}} or {{node_123.text}}
        import re
        pattern = re.compile(r"\{\{([^}]+)\}\}")
        
        def replace(match):
            key = match.group(1).strip()
            val = self._get_nested_value(state, key)
            return str(val) if val is not None else ""
            
        return pattern.sub(replace, text)

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        parts = path.split(".")
        curr = data
        for part in parts:
            if isinstance(curr, dict):
                curr = curr.get(part)
            else:
                return None
        return curr
