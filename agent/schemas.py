"""
Pydantic models for the Chat / Agent endpoints.
"""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    message: str
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    thread_id: str = "default"


class ChatResponse(BaseModel):
    """Response body for POST /chat."""

    answer: str
    related_node_ids: list[str] = Field(default_factory=list)
    highlight_ids: list[str] = Field(default_factory=list)
    tool_calls_made: list[str] = Field(default_factory=list)


class ExplainRequest(BaseModel):
    """Request body for POST /kg/explain."""

    node_id: str
    node_type: str  # "Incident" | "Category" | "Municipality" | "LocationCluster"


class ExplainResponse(BaseModel):
    """Response body for POST /kg/explain."""

    explanation: str
    related_nodes: list[dict] = Field(default_factory=list)
    highlight_ids: list[str] = Field(default_factory=list)
