"""
SafeRoad CrewAI Crew — Senaryo B: KG Enrichment.

3 ajanlı sequential crew:
  1. Classifier Agent  — LLM ile sınıflandırma (tool yok)
  2. Graph Analyst Agent — Neo4j'den mekansal analiz
  3. Graph Updater Agent — Neo4j'i güncelle

SYNC — crew.kickoff(inputs) fonksiyonu asyncio event loop'u olmayan
bir thread pool executor (run_in_executor) içinde çağrılmalıdır.
"""

import logging

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from agent.crew_tools import (
    neo4j_query_tool,
    find_nearby_incidents_tool,
    get_cluster_info_tool,
    neo4j_write_tool,
    update_cluster_tool,
    update_municipality_weight_tool,
    create_similar_to_tool,
)
from core.config import settings

logger = logging.getLogger(__name__)


def _make_llm() -> ChatOpenAI:
    """gpt-4o-mini LLM instance oluşturur. settings lazy proxy — import zamanında güvenli."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.openai_api_key,
        temperature=0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 1: Classifier Agent
# ─────────────────────────────────────────────────────────────────────────────

classifier_agent = Agent(
    role="Traffic Incident Classifier",
    goal=(
        "Analyze the incoming traffic incident and produce a JSON classification:\n"
        "- confirmed_category: one of Pothole / Flooding / Accident / Roadwork / Other\n"
        "- severity: low | medium | high | critical\n"
        "- urgency_score: float between 0.0 and 1.0\n"
        "- keywords: list of key terms extracted from the description"
    ),
    backstory=(
        "You are an expert analyst in Turkish traffic safety data. "
        "You quickly determine the correct category and severity from incident title and description."
    ),
    llm=_make_llm(),
    tools=[],  # Saf LLM reasoning — tool gerekmez
    verbose=False,
)

classify_task = Task(
    description=(
        "Classify the following traffic incident. Respond with VALID JSON ONLY — no extra text.\n\n"
        "Title: {title}\n"
        "Description: {description}\n"
        "Reported Category: {category}\n"
        "Location: lat={lat}, lng={lng}\n\n"
        'Output format:\n{{"confirmed_category": "...", "severity": "...", "urgency_score": 0.0, "keywords": ["..."]}}'
    ),
    expected_output="Valid JSON object with confirmed_category, severity, urgency_score, keywords",
    agent=classifier_agent,
)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 2: Graph Analyst Agent
# ─────────────────────────────────────────────────────────────────────────────

graph_analyst_agent = Agent(
    role="Knowledge Graph Analyst",
    goal=(
        "Using Neo4j tools, analyze spatial patterns around the new incident:\n"
        "1. Find incidents within 500m of the same category\n"
        "2. Find the nearest existing LocationCluster\n"
        "3. Retrieve the current risk score of this area\n"
        "4. Determine the 30-day incident trend (increasing/decreasing/stable)"
    ),
    backstory=(
        "You are a graph database and spatial analysis expert. "
        "You write efficient Cypher queries to extract patterns from Neo4j."
    ),
    llm=_make_llm(),
    tools=[neo4j_query_tool, find_nearby_incidents_tool, get_cluster_info_tool],
    verbose=False,
)

analyze_task = Task(
    description=(
        "Using the classification result from the previous step, analyze Neo4j.\n\n"
        "Incident ID: {incident_id}\n"
        "Coordinates: lat={lat}, lng={lng}\n\n"
        "Find:\n"
        "1. Similar incidents within 500m\n"
        "2. Nearest LocationCluster (use get_cluster_info tool)\n"
        "3. Municipality risk score in this area\n"
        "4. 30-day incident trend\n\n"
        "Produce a concise analysis report."
    ),
    expected_output=(
        "Spatial analysis report including: nearby incidents list, "
        "nearest cluster id (or 'none'), area risk score, 30-day trend"
    ),
    agent=graph_analyst_agent,
    context=[classify_task],  # Classifier çıktısını alır
)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 3: Graph Updater Agent
# ─────────────────────────────────────────────────────────────────────────────

graph_updater_agent = Agent(
    role="Knowledge Graph Updater",
    goal=(
        "Based on Classifier and Analyst outputs, update Neo4j:\n"
        "1. SET severity and urgency_score on the Incident node\n"
        "2. Link incident to nearest cluster or create a new LocationCluster\n"
        "3. Create SIMILAR_TO relationships with up to 3 similar incidents\n"
        "4. Recalculate Municipality weight\n"
        "Always use MERGE, never CREATE, to prevent duplicates."
    ),
    backstory=(
        "You are a Neo4j data model expert. "
        "You keep the Knowledge Graph consistent and up-to-date using MERGE operations."
    ),
    llm=_make_llm(),
    tools=[
        neo4j_write_tool,
        update_cluster_tool,
        update_municipality_weight_tool,
        create_similar_to_tool,
    ],
    verbose=False,
)

update_task = Task(
    description=(
        "Update Neo4j based on the classifier and analyst results.\n\n"
        "Incident ID: {incident_id}\n\n"
        "Steps (in order):\n"
        "1. Call neo4j_write_tool with severity and urgency_score from classifier output\n"
        "2. If analyst found a cluster: call update_cluster_tool with existing cluster_id\n"
        "   If no cluster found: call update_cluster_tool with empty cluster_id and lat={lat}, lng={lng}\n"
        "3. For up to 3 similar incidents found by analyst: call create_similar_to_tool\n"
        "4. Call update_municipality_weight_tool with the municipality_id from analyst output\n"
        "   (query Neo4j first if municipality_id is unknown: "
        "MATCH (i:Incident {{id: '{incident_id}'}})-[:IN_MUNICIPALITY]->(m) RETURN m.id)\n\n"
        "Return a summary of all updates made."
    ),
    expected_output=(
        "Update summary: severity set, cluster linked/created, "
        "SIMILAR_TO relationships created, municipality weight updated"
    ),
    agent=graph_updater_agent,
    context=[classify_task, analyze_task],  # Her iki önceki çıktıyı alır
)


# ─────────────────────────────────────────────────────────────────────────────
# CREW
# ─────────────────────────────────────────────────────────────────────────────

crew = Crew(
    agents=[classifier_agent, graph_analyst_agent, graph_updater_agent],
    tasks=[classify_task, analyze_task, update_task],
    process=Process.sequential,  # Bağımlılık zinciri — paralel değil
    verbose=False,
)
