"""
SafeRoad CrewAI Crew — Senaryo B: KG Enrichment.

3 ajanlı sequential crew. Agent ve task tanımları
agent/config/agents.yaml ve config/tasks.yaml'dan yüklenir.

SYNC — crew.kickoff(inputs) fonksiyonu asyncio event loop'u olmayan
bir thread pool executor (run_in_executor) içinde çağrılmalıdır.
"""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew as crew_decorator, task
from langchain_openai import ChatOpenAI

from agent.crew_tools import (
    create_similar_to_tool,
    find_nearby_incidents_tool,
    get_cluster_info_tool,
    neo4j_query_tool,
    neo4j_write_tool,
    update_cluster_tool,
    update_municipality_weight_tool,
)
from core.config import settings

logger = logging.getLogger(__name__)


def _make_llm() -> ChatOpenAI:
    """LLM instance oluşturur. Model adı settings'ten okunur."""
    return ChatOpenAI(
        model=settings.crew_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )


@CrewBase
class SafeRoadCrew:
    """YAML config'den yüklenen 3-ajanlı sequential KG Enrichment crew."""

    # @CrewBase bu yolları bu dosyanın bulunduğu dizine (agent/) göre çözümler
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ── Agents ────────────────────────────────────────────────

    @agent
    def classifier_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["classifier_agent"],
            llm=_make_llm(),
            tools=[],
            verbose=False,
        )

    @agent
    def graph_analyst_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["graph_analyst_agent"],
            llm=_make_llm(),
            tools=[neo4j_query_tool, find_nearby_incidents_tool, get_cluster_info_tool],
            verbose=False,
        )

    @agent
    def graph_updater_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["graph_updater_agent"],
            llm=_make_llm(),
            tools=[
                neo4j_write_tool,
                update_cluster_tool,
                update_municipality_weight_tool,
                create_similar_to_tool,
            ],
            verbose=False,
        )

    # ── Tasks ─────────────────────────────────────────────────

    @task
    def classify_task(self) -> Task:
        return Task(config=self.tasks_config["classify_task"])

    @task
    def analyze_task(self) -> Task:
        return Task(config=self.tasks_config["analyze_task"])

    @task
    def update_task(self) -> Task:
        return Task(config=self.tasks_config["update_task"])

    # ── Crew ──────────────────────────────────────────────────

    @crew_decorator
    def build_crew(self) -> Crew:
        return Crew(
            agents=self.agents,   # @CrewBase @agent metodlarından otomatik toplar
            tasks=self.tasks,     # @CrewBase @task metodlarından otomatik toplar
            process=Process.sequential,
            verbose=False,
        )


# Module-level singleton — routers/crew.py'deki `from agent.crew import crew` korunur
crew = SafeRoadCrew().build_crew()
