"""The real event source: an ADK Runner driving the Gemini-backed agent."""

from collections.abc import AsyncGenerator

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent.agent import KICKOFF_MESSAGE, build_agent
from app.agent.callbacks import RunRecord
from app.config import MAX_LLM_CALLS
from app.simulation.engine import SimulationEngine

APP_NAME = "resilience-arena"
USER_ID = "demo"


async def adk_event_source(engine: SimulationEngine, record: RunRecord) -> AsyncGenerator:
    agent = build_agent(engine, record)
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    runner = Runner(app_name=APP_NAME, agent=agent, session_service=session_service)
    message = types.Content(role="user", parts=[types.Part(text=KICKOFF_MESSAGE)])
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=message,
        run_config=RunConfig(max_llm_calls=MAX_LLM_CALLS),
    ):
        yield event
