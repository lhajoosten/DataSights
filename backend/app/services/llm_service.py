"""
LLM service for natural language processing and chart specification generation.
Similar to an external service integration in .NET applications.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import openai
from openai import AsyncOpenAI

from app.models.chat_models import LLMRequest, LLMResponse, ChatMessage
from app.models.chart_models import ChartSpec
from app.models.csv_models import CSVMetadata
from app.core.config import get_settings
from app.core.exceptions import LLMServiceException

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for LLM integration and chart specification generation.
    Handles OpenAI API integration with fallback strategies.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize OpenAI client if API key is available."""
        if self.settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        else:
            logger.warning("No OpenAI API key provided. LLM service will use fallback mode.")
    
    async def generate_chart_spec(
        self, 
        question: str, 
        csv_metadata: CSVMetadata,
        context: Optional[List[ChatMessage]] = None
    ) -> LLMResponse:
        """
        Generate chart specification from natural language question.
        
        Args:
            question: User's natural language question
            csv_metadata: Metadata about the CSV file
            context: Previous chat context for follow-up questions
            
        Returns:
            LLMResponse with chart specification or clarification request
        """
        start_time = datetime.now()
        
        try:
            if self.client:
                response = await self._call_openai_api(question, csv_metadata, context)
            else:
                response = await self._fallback_response(question, csv_metadata)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            response.processing_time_ms = processing_time
            
            return response
            
        except Exception as e:
            logger.error(f"LLM service error: {str(e)}", exc_info=True)
            
            # Return fallback response on error
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return await self._error_fallback_response(question, processing_time)
    
    async def _call_openai_api(
        self, 
        question: str, 
        csv_metadata: CSVMetadata,
        context: Optional[List[ChatMessage]] = None
    ) -> LLMResponse:
        """Call OpenAI API with structured prompts."""
        try:
            system_prompt = self._build_system_prompt(csv_metadata)
            user_prompt = self._build_user_prompt(question, csv_metadata)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Add context if provided
            if context:
                for msg in context[-5:]:  # Limit context to last 5 messages
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Call OpenAI API
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.settings.openai_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=1000,
                    response_format={"type": "json_object"}
                ),
                timeout=self.settings.llm_timeout_seconds
            )
            
            content = response.choices[0].message.content
            return await self._parse_llm_response(content, question)
            
        except asyncio.TimeoutError:
            raise LLMServiceException("LLM request timed out")
        except openai.AuthenticationError:
            raise LLMServiceException("Invalid OpenAI API key")
        except openai.RateLimitError:
            raise LLMServiceException("OpenAI API rate limit exceeded")
        except Exception as e:
            raise LLMServiceException(f"OpenAI API error: {str(e)}")
    
    async def _parse_llm_response(self, content: str, original_question: str) -> LLMResponse:
        """Parse and validate LLM response content."""
        try:
            parsed_content = json.loads(content)
            
            # Check if response requires clarification
            if parsed_content.get("requires_clarification", False):
                return LLMResponse(
                    content=parsed_content.get("explanation", "I need more information to answer your question."),
                    requires_clarification=True,
                    clarification_question=parsed_content.get("clarification_question", 
                                                             "Could you please provide more details about what you'd like to visualize?"),
                    processing_time_ms=0  # Will be set by caller
                )
            
            # Try to extract chart specification
            chart_spec_data = parsed_content.get("chart_spec")
            if chart_spec_data:
                try:
                    # Validate chart spec using Pydantic
                    chart_spec = ChartSpec(**chart_spec_data)
                    
                    return LLMResponse(
                        content=parsed_content.get("explanation", "Here's your chart visualization."),
                        chart_spec=chart_spec.model_dump(),  # Use model_dump() instead of dict()
                        requires_clarification=False,
                        processing_time_ms=0  # Will be set by caller
                    )
                except Exception as validation_error:
                    logger.warning(f"Chart spec validation failed: {str(validation_error)}")
                    return LLMResponse(
                        content="I created a chart specification but it had validation errors. Let me try a different approach.",
                        requires_clarification=True,
                        clarification_question="Could you try asking for a simpler visualization, like a basic bar chart or line chart?",
                        processing_time_ms=0
                    )
            else:
                # No chart spec but valid response
                return LLMResponse(
                    content=parsed_content.get("explanation", "I understand your question but couldn't generate a chart specification."),
                    requires_clarification=True,
                    clarification_question="Could you rephrase your question to be more specific about the visualization you want?",
                    processing_time_ms=0
                )
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {content}, Error: {str(e)}")
            return LLMResponse(
                content="I had trouble understanding how to visualize your data. Could you rephrase your question?",
                requires_clarification=True,
                clarification_question="What specific chart or visualization would you like to see?",
                processing_time_ms=0
            )
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return LLMResponse(
                content="I encountered an error processing your request. Please try a different question.",
                requires_clarification=True,
                clarification_question="Could you try asking about a specific chart type or data analysis?",
                processing_time_ms=0
            )
    
    def _build_system_prompt(self, csv_metadata: CSVMetadata) -> str:
        """Build system prompt with CSV schema information."""
        numeric_cols = csv_metadata.get_numeric_columns()
        categorical_cols = csv_metadata.get_categorical_columns()
        datetime_cols = csv_metadata.get_datetime_columns()
        
        return f"""You are a data visualization assistant. Your job is to interpret user questions about CSV data and generate chart specifications.

CSV Data Schema:
- Total rows: {csv_metadata.row_count:,}
- Total columns: {len(csv_metadata.columns)}
- Numeric columns: {numeric_cols}
- Categorical columns: {categorical_cols}
- Datetime columns: {datetime_cols}

Column types: {json.dumps(csv_metadata.column_types, indent=2)}

Rules:
1. Always respond with valid JSON containing either a chart_spec or clarification request
2. For unclear questions, set requires_clarification=true and ask a specific follow-up question
3. Only suggest charts that make sense with the available data
4. Limit group_by to maximum 3 columns for readability
5. Use simple aggregations: sum, mean, count, min, max
6. Prefer bar charts for categorical data, line charts for time series, scatter for correlations

Response format:
{{
  "explanation": "Human-readable explanation",
  "requires_clarification": false,
  "clarification_question": null,
  "chart_spec": {{
    "chart_type": "bar|line|scatter|pie",
    "x": "column_name",
    "y": "column_name", 
    "aggregation": "sum|mean|count|min|max|none",
    "group_by": ["column1", "column2"],
    "filters": [
      {{"column": "col", "operator": "==", "value": "val"}}
    ],
    "explanation": "Chart explanation",
    "title": "Chart title"
  }}
}}"""
    
    def _build_user_prompt(self, question: str, csv_metadata: CSVMetadata) -> str:
        """Build user prompt with question and context."""
        return f"""User question: "{question}"

Please analyze this question in the context of the provided CSV data schema and generate an appropriate chart specification. If the question is ambiguous or cannot be answered with the available data, request clarification instead."""
    
    async def _fallback_response(self, question: str, csv_metadata: CSVMetadata) -> LLMResponse:
        """
        Provide fallback response when OpenAI API is not available.
        Uses simple heuristics to suggest basic visualizations.
        """
        logger.info("Using fallback LLM response (no API key configured)")
        
        question_lower = question.lower()
        numeric_cols = csv_metadata.get_numeric_columns()
        categorical_cols = csv_metadata.get_categorical_columns()
        datetime_cols = csv_metadata.get_datetime_columns()
        
        # Simple heuristics for common chart types
        if any(word in question_lower for word in ['trend', 'over time', 'time series']) and datetime_cols and numeric_cols:
            chart_spec = {
                "chart_type": "line",
                "x": datetime_cols[0],
                "y": numeric_cols[0],
                "aggregation": "none",
                "explanation": f"Line chart showing {numeric_cols[0]} over {datetime_cols[0]}",
                "title": f"{numeric_cols[0]} Over Time"
            }
        elif any(word in question_lower for word in ['compare', 'by category', 'breakdown']) and categorical_cols and numeric_cols:
            chart_spec = {
                "chart_type": "bar",
                "x": categorical_cols[0],
                "y": numeric_cols[0],
                "aggregation": "sum",
                "explanation": f"Bar chart comparing {numeric_cols[0]} by {categorical_cols[0]}",
                "title": f"{numeric_cols[0]} by {categorical_cols[0]}"
            }
        elif any(word in question_lower for word in ['correlation', 'relationship']) and len(numeric_cols) >= 2:
            chart_spec = {
                "chart_type": "scatter",
                "x": numeric_cols[0],
                "y": numeric_cols[1],
                "aggregation": "none",
                "explanation": f"Scatter plot showing relationship between {numeric_cols[0]} and {numeric_cols[1]}",
                "title": f"{numeric_cols[0]} vs {numeric_cols[1]}"
            }
        else:
            # Request clarification for unclear questions
            return LLMResponse(
                content="I need more information to create a visualization for your data.",
                requires_clarification=True,
                clarification_question=f"What would you like to visualize? Available numeric columns: {numeric_cols}, categorical columns: {categorical_cols}",
                processing_time_ms=0
            )
        
        return LLMResponse(
            content=f"Here's a suggested visualization based on your question: {chart_spec['explanation']}",
            chart_spec=chart_spec,
            requires_clarification=False,
            processing_time_ms=0
        )
    
    async def _error_fallback_response(self, question: str, processing_time: float) -> LLMResponse:
        """Provide error fallback response when LLM service fails."""
        return LLMResponse(
            content="I'm having trouble processing your request right now. Please try a simpler question about your data.",
            requires_clarification=True,
            clarification_question="Would you like to see a basic chart of your data? For example, 'show me a bar chart' or 'show me trends over time'?",
            processing_time_ms=processing_time
        )