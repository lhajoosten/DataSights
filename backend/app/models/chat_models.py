"""
Chat and LLM interaction models.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Individual chat message."""
    
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Show me sales by month",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class ChatRequest(BaseModel):
    """Request to ask a question about uploaded CSV data."""
    
    file_id: str = Field(..., description="ID of uploaded CSV file")
    question: str = Field(
        ..., 
        min_length=3,
        max_length=1000,
        description="Natural language question about the data"
    )
    context: Optional[List[ChatMessage]] = Field(
        None, description="Previous chat context for follow-up questions"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "csv_12345",
                "question": "Show me total sales by month for 2024",
                "context": []
            }
        }


class ChatResponse(BaseModel):
    """Response from chat question processing."""
    
    message: ChatMessage = Field(..., description="Assistant's response message")
    chart_data: Optional[Dict[str, Any]] = Field(
        None, description="Chart data if question resulted in visualization"
    )
    requires_clarification: bool = Field(
        False, description="Whether question needs clarification"
    )
    clarification_prompt: Optional[str] = Field(
        None, description="Clarification question for user"
    )
    suggested_questions: List[str] = Field(
        default_factory=list, description="Suggested follow-up questions"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": {
                    "role": "assistant",
                    "content": "Here's a bar chart showing total sales by month for 2024",
                    "timestamp": "2024-01-01T12:00:00Z"
                },
                "chart_data": {
                    "chart_type": "bar",
                    "data": [{"month": "Jan", "sales": 1000}]
                },
                "requires_clarification": False,
                "suggested_questions": [
                    "Show sales by region",
                    "Compare with previous year"
                ]
            }
        }


class LLMRequest(BaseModel):
    """Internal request to LLM service."""
    
    system_prompt: str = Field(..., description="System instruction for LLM")
    user_prompt: str = Field(..., description="User question/prompt")
    csv_schema: Dict[str, Any] = Field(..., description="CSV column information")
    context: Optional[List[ChatMessage]] = Field(None, description="Chat context")
    temperature: float = Field(0.1, description="LLM temperature setting")
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_prompt": "You are a data visualization assistant...",
                "user_prompt": "Show sales by month",
                "csv_schema": {
                    "columns": ["date", "sales", "region"],
                    "types": {"date": "datetime", "sales": "float", "region": "string"}
                },
                "temperature": 0.1
            }
        }


class LLMResponse(BaseModel):
    """Response from LLM service."""
    
    content: str = Field(..., description="Raw LLM response content")
    chart_spec: Optional[Dict[str, Any]] = Field(
        None, description="Parsed chart specification"
    )
    requires_clarification: bool = Field(False, description="Whether clarification needed")
    clarification_question: Optional[str] = Field(None, description="Clarification question")
    processing_time_ms: float = Field(..., description="LLM processing time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "I'll create a bar chart showing sales by month",
                "chart_spec": {
                    "chart_type": "bar",
                    "x": "month",
                    "y": "sales"
                },
                "requires_clarification": False,
                "processing_time_ms": 1250.5
            }
        }