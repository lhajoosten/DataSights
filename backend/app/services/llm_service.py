"""
Simplified LLM service with clear prompts and structured responses.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import openai
from openai import AsyncOpenAI

from app.models.chat_models import LLMResponse, ChatMessage
from app.models.chart_models import ChartSpec
from app.models.csv_models import CSVMetadata
from app.core.config import get_settings
from app.core.exceptions import LLMServiceException

logger = logging.getLogger(__name__)


class LLMService:
    """
    Simple, reliable LLM service with fixed parsing.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize OpenAI client if API key is available."""
        if self.settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("No OpenAI API key - using fallback mode")
    
    async def generate_chart_spec(
        self, 
        question: str, 
        csv_metadata: CSVMetadata,
        context: Optional[List[ChatMessage]] = None
    ) -> LLMResponse:
        """
        Main entry point: Generate chart specification from natural language.
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing question: '{question}'")
            logger.info(f"Available columns: {csv_metadata.columns}")
            
            if self.client:
                response = await self._call_openai_api(question, csv_metadata, context)
            else:
                response = self._create_fallback_response(question, csv_metadata)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            response.processing_time_ms = processing_time
            
            logger.info(f"Generated response in {processing_time:.1f}ms")
            return response
            
        except Exception as e:
            logger.error(f"LLM service error: {str(e)}", exc_info=True)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return self._create_error_response(question, processing_time)
    
    async def _call_openai_api(
        self, 
        question: str, 
        csv_metadata: CSVMetadata,
        context: Optional[List[ChatMessage]] = None
    ) -> LLMResponse:
        """Call OpenAI API with simple, clear prompts."""
        try:
            messages = [
                {"role": "system", "content": self._build_system_prompt(csv_metadata)},
                {"role": "user", "content": self._build_user_prompt(question)}
            ]
            
            # Add context (last 3 messages only)
            if context:
                for msg in context[-3:]:
                    messages.append({"role": msg.role, "content": msg.content})
            
            # Call OpenAI with timeout
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.settings.openai_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=1000,
                    response_format={"type": "json_object"}
                ),
                timeout=30
            )
            
            content = response.choices[0].message.content
            logger.info(f"OpenAI response: {content[:200]}...")  # Log first 200 chars
            
            return self._parse_openai_response(content)
            
        except asyncio.TimeoutError:
            logger.error("OpenAI API timeout")
            raise LLMServiceException("Request timed out")
        except openai.AuthenticationError:
            logger.error("OpenAI authentication failed")
            raise LLMServiceException("Invalid API key")
        except openai.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            raise LLMServiceException("Rate limit exceeded")
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMServiceException(f"API error: {str(e)}")
    
    def _build_system_prompt(self, csv_metadata: CSVMetadata) -> str:
        """Enhanced system prompt for better multi-dimensional understanding."""
        numeric_cols = csv_metadata.get_numeric_columns()
        categorical_cols = csv_metadata.get_categorical_columns()
        datetime_cols = csv_metadata.get_datetime_columns()
        
        return f"""You are a data visualization expert. Create chart specifications for complex, multi-dimensional data analysis.

        DATASET INFO:
        - Rows: {csv_metadata.row_count:,}
        - Columns: {csv_metadata.columns}
        - Numeric: {numeric_cols}
        - Categories: {categorical_cols}
        - Dates: {datetime_cols}

        ADVANCED PATTERNS:
        1. **Multi-dimensional grouping**: "by region and product" → use group_by: ["region", "product"]
        2. **Time comparisons**: "over time by region" → group_by: ["region"] + time extraction
        3. **Calculated fields**: "revenue" → calculate from units_sold * unit_price

        RESPOND WITH JSON:
        {{
        "explanation": "Brief description",
        "chart_spec": {{
            "chart_type": "bar|line",
            "x": "primary_dimension",
            "y": "metric_column", 
            "aggregation": "sum",
            "group_by": ["secondary_dimension"],
            "calculation": {{
            "field_name": "revenue",
            "formula": "units_sold * unit_price",
            "description": "Revenue calculation"
            }},
            "title": "Descriptive Title"
        }}
        }}

        EXAMPLES:
        - "units sold by region and product" → x: "region", group_by: ["product"]
        - "revenue by product across regions" → x: "product", group_by: ["region"], calculation: revenue
        - "compare by region over time" → x: "date", group_by: ["region"]

        Available columns: {csv_metadata.columns}"""

    def _build_user_prompt(self, question: str) -> str:
        """Build simple user prompt."""
        return f"""Question: "{question}"

Create a chart specification to answer this question. Respond with JSON only."""
    
    def _parse_openai_response(self, content: str) -> LLMResponse:
        """Parse OpenAI response with robust error handling."""
        try:
            data = json.loads(content)
            logger.info(f"Parsed JSON: {data}")
            
            # Check for clarification request
            if data.get("requires_clarification", False):
                return LLMResponse(
                    content=data.get("explanation", "Need more information"),
                    chart_spec=None,
                    requires_clarification=True,
                    clarification_question=data.get("clarification_question", "Please clarify your question"),
                    processing_time_ms=0
                )
            
            # Extract chart spec
            chart_spec_data = data.get("chart_spec")
            if chart_spec_data:
                try:
                    # Add explanation to chart_spec if missing
                    if "explanation" not in chart_spec_data:
                        chart_spec_data["explanation"] = data.get("explanation", "Data visualization")
                    
                    logger.info(f"Creating ChartSpec with: {chart_spec_data}")
                    chart_spec = ChartSpec(**chart_spec_data)
                    
                    return LLMResponse(
                        content=data.get("explanation", "Here's your chart"),
                        chart_spec=chart_spec.model_dump(),
                        requires_clarification=False,
                        clarification_question=None,
                        processing_time_ms=0
                    )
                except Exception as e:
                    logger.error(f"Chart spec validation failed: {str(e)}")
                    logger.error(f"Failed chart_spec_data: {chart_spec_data}")
                    
                    # Try with minimal data
                    try:
                        minimal_spec = {
                            "chart_type": chart_spec_data.get("chart_type", "bar"),
                            "x": chart_spec_data.get("x"),
                            "y": chart_spec_data.get("y"),
                            "aggregation": chart_spec_data.get("aggregation", "sum"),
                            "explanation": data.get("explanation", "Data visualization")
                        }
                        logger.info(f"Trying minimal spec: {minimal_spec}")
                        chart_spec = ChartSpec(**minimal_spec)
                        
                        return LLMResponse(
                            content=data.get("explanation", "Here's your chart"),
                            chart_spec=chart_spec.model_dump(),
                            requires_clarification=False,
                            clarification_question=None,
                            processing_time_ms=0
                        )
                    except Exception as e2:
                        logger.error(f"Minimal spec also failed: {str(e2)}")
            
            # No valid chart spec
            return self._create_clarification_response("Couldn't generate chart. Please rephrase your question.")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse OpenAI response as JSON: {str(e)}")
            logger.warning(f"Raw content: {content}")
            return self._create_clarification_response("Had trouble understanding. Please rephrase your question.")
        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {str(e)}")
            return self._create_clarification_response("Processing error. Please try again.")
    
    def _create_fallback_response(self, question: str, csv_metadata: CSVMetadata) -> LLMResponse:
        """Simple fallback when OpenAI is not available."""
        logger.info("Using fallback response")
        
        question_lower = question.lower()
        numeric_cols = csv_metadata.get_numeric_columns()
        categorical_cols = csv_metadata.get_categorical_columns()
        
        # Simple patterns
        if 'region' in question_lower and 'units_sold' in csv_metadata.columns:
            chart_spec = {
                "chart_type": "bar",
                "x": "region",
                "y": "units_sold",
                "aggregation": "sum",
                "explanation": "Units sold by region",
                "title": "Units Sold by Region"
            }
            
            if 'product' in question_lower:
                chart_spec["group_by"] = ["region", "product"]
                chart_spec["explanation"] = "Units sold by region and product"
                chart_spec["title"] = "Units Sold by Region and Product"
            
            return LLMResponse(
                content=chart_spec["explanation"],
                chart_spec=chart_spec,
                requires_clarification=False,
                clarification_question=None,
                processing_time_ms=0
            )
        
        # Generic fallback
        elif categorical_cols and numeric_cols:
            chart_spec = {
                "chart_type": "bar",
                "x": categorical_cols[0],
                "y": numeric_cols[0],
                "aggregation": "sum",
                "explanation": f"{numeric_cols[0]} by {categorical_cols[0]}",
                "title": f"{numeric_cols[0]} by {categorical_cols[0]}"
            }
            
            return LLMResponse(
                content=chart_spec["explanation"],
                chart_spec=chart_spec,
                requires_clarification=False,
                clarification_question=None,
                processing_time_ms=0
            )
        
        # Need clarification
        else:
            return self._create_clarification_response(
                f"Available data: {', '.join(csv_metadata.columns[:5])}. What would you like to visualize?"
            )
    
    def _create_clarification_response(self, message: str) -> LLMResponse:
        """Create a clarification response."""
        return LLMResponse(
            content="I need more information to create a visualization.",
            chart_spec=None,
            requires_clarification=True,
            clarification_question=message,
            processing_time_ms=0
        )
    
    def _create_error_response(self, question: str, processing_time: float) -> LLMResponse:
        """Create error response."""
        return LLMResponse(
            content="Sorry, I encountered an error processing your request.",
            chart_spec=None,
            requires_clarification=True,
            clarification_question="Please try a simpler question about your data.",
            processing_time_ms=processing_time
        )