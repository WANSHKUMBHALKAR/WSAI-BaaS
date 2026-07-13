"""
Multi-agent orchestrator.

Enables chaining multiple specialized agents:
  supervisor → [research_agent, writer_agent, reviewer_agent] → final answer
"""
from __future__ import annotations

import logging
from typing import Optional

from app.agents.runtime import AgentRuntime

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Runs a pipeline of agents where the output of one feeds the next.
    """

    def __init__(self, agents: list[AgentRuntime]) -> None:
        self.agents = agents

    async def run_pipeline(self, initial_input: str) -> dict:
        """Chain agents sequentially — each gets the previous output as input."""
        current_input = initial_input
        history: list[dict] = []

        for i, agent in enumerate(self.agents):
            logger.info("Orchestrator: running agent %d/%d (id=%s)", i + 1, len(self.agents), agent.agent_id)
            result = await agent.run(current_input)
            history.append({"agent_id": agent.agent_id, "result": result})
            current_input = result["response"]

        return {
            "final_response": current_input,
            "pipeline": history,
            "agents_count": len(self.agents),
        }

    async def run_parallel(self, inputs: list[str]) -> list[dict]:
        """Run multiple agents concurrently with independent inputs."""
        import asyncio
        if len(inputs) != len(self.agents):
            raise ValueError("Number of inputs must match number of agents")
        tasks = [agent.run(inp) for agent, inp in zip(self.agents, inputs)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            {"agent_id": agent.agent_id, "result": r if not isinstance(r, Exception) else str(r)}
            for agent, r in zip(self.agents, results)
        ]
