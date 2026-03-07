"""
Chat endpoint — POST /chat
Delegates natural language queries to the LangGraph ReAct agent.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent.graph import get_agent
from agent.schemas import ChatRequest, ChatResponse
from core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    """
    Send a message to the SafeRoad AI Assistant.
    Optionally include conversation_history for multi-turn context.
    """
    # Build message list from history
    messages = []
    for msg in request.conversation_history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))
        elif msg.role == "system":
            messages.append(SystemMessage(content=msg.content))

    # Add the new user message
    messages.append(HumanMessage(content=request.message))

    # Invoke the agent
    try:
        agent = get_agent()
        result = await agent.ainvoke(
            {
                "messages": messages,
                "highlight_ids": [],
                "related_node_ids": [],
                "tool_calls_made": [],
                "iteration_count": 0,
            },
        )
    except Exception as e:
        logger.error("Agent invocation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI agent encountered an error. Please try again.",
        )

    # Extract answer from last AI message
    result_messages = result.get("messages", [])
    answer = "I couldn't generate a response. Please try again."
    for msg in reversed(result_messages):
        if isinstance(msg, AIMessage) and msg.content:
            answer = msg.content
            break

    return ChatResponse(
        answer=answer,
        related_node_ids=result.get("related_node_ids", []),
        highlight_ids=result.get("highlight_ids", []),
        tool_calls_made=result.get("tool_calls_made", []),
    )
