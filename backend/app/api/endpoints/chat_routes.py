"""
Chat and chart generation endpoints.
Similar to a ChatController in .NET Web API for conversational interfaces.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timezone

from app.services.csv_service import CSVService
from app.services.llm_service import LLMService
from app.services.chart_service import ChartService
from app.services.file_storage_service import FileStorageService
from app.models.chat_models import ChatRequest, ChatResponse, ChatMessage
from app.models.chart_models import ChartSpec, ChartData
from app.core.exceptions import ValidationException, FileProcessingException, LLMServiceException

logger = logging.getLogger(__name__)
router = APIRouter()


# Dependency injection - similar to .NET DI pattern
def get_csv_service() -> CSVService:
    return CSVService()


def get_llm_service() -> LLMService:
    return LLMService()


def get_chart_service() -> ChartService:
    return ChartService()


def get_file_storage_service() -> FileStorageService:
    return FileStorageService()


@router.post("/ask", response_model=ChatResponse)
async def ask_question_about_data(
    request: ChatRequest,
    csv_service: CSVService = Depends(get_csv_service),
    llm_service: LLMService = Depends(get_llm_service),
    chart_service: ChartService = Depends(get_chart_service),
    file_storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Process natural language question about uploaded CSV data.
    
    Similar to a POST action in .NET Web API for complex business operations.
    Orchestrates multiple services to generate chart from user question.
    """
    logger.info(f"Chat request: file_id={request.file_id}, question='{request.question}'")
    
    try:
        # Get file path and verify file exists
        file_path = await file_storage.get_file_path(request.file_id)
        
        # Get CSV metadata for LLM context
        csv_metadata = await csv_service.get_csv_metadata(file_path, request.file_id)
        
        # Process question with LLM service
        llm_response = await llm_service.generate_chart_spec(
            question=request.question,
            csv_metadata=csv_metadata,
            context=request.context
        )
        
        # Create assistant message
        assistant_message = ChatMessage(
            role="assistant",
            content=llm_response.content,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # If LLM needs clarification, return early
        if llm_response.requires_clarification:
            logger.info(f"LLM requested clarification for: {request.question}")
            
            return ChatResponse(
                message=assistant_message,
                requires_clarification=True,
                clarification_prompt=llm_response.clarification_question,
                suggested_questions=_generate_suggested_questions(csv_metadata)
            )
        
        # Generate chart if we have a valid chart spec
        chart_data = None
        if llm_response.chart_spec:
            try:
                # Parse chart specification
                chart_spec = ChartSpec(**llm_response.chart_spec)
                
                # Load DataFrame for chart generation
                dataframe = await csv_service.load_dataframe(file_path)
                
                # Generate chart data
                chart_result = await chart_service.generate_chart_data(
                    chart_spec=chart_spec,
                    dataframe=dataframe,
                    csv_metadata=csv_metadata
                )
                
                chart_data = chart_result.dict()
                
                logger.info(f"Chart generated successfully: {chart_spec.chart_type}")
                
            except ValidationException as ve:
                # Chart validation failed - ask for clarification
                logger.warning(f"Chart validation failed: {ve.message}")
                
                return ChatResponse(
                    message=ChatMessage(
                        role="assistant",
                        content=f"I couldn't create that visualization: {ve.message}",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ),
                    requires_clarification=True,
                    clarification_prompt=ve.details.get("suggestions", ["Please try a different question"])[0] if ve.details else "Could you rephrase your question?",
                    suggested_questions=_generate_suggested_questions(csv_metadata)
                )
            
            except Exception as chart_error:
                logger.error(f"Chart generation error: {str(chart_error)}", exc_info=True)
                
                return ChatResponse(
                    message=ChatMessage(
                        role="assistant", 
                        content="I encountered an error generating your chart. Please try a simpler question.",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    ),
                    requires_clarification=True,
                    clarification_prompt="What type of chart would you like to see with your data?",
                    suggested_questions=_generate_suggested_questions(csv_metadata)
                )
        
        # Return successful response with chart data
        return ChatResponse(
            message=assistant_message,
            chart_data=chart_data,
            requires_clarification=False,
            suggested_questions=_generate_suggested_questions(csv_metadata)
        )
        
    except FileProcessingException as e:
        logger.warning(f"File not found for chat request: {request.file_id}")
        raise HTTPException(status_code=404, detail={
            "error": f"CSV file not found: {request.file_id}",
            "type": "FileNotFound"
        })
    
    except LLMServiceException as e:
        logger.error(f"LLM service error: {e.message}")
        raise HTTPException(status_code=503, detail={
            "error": "LLM service temporarily unavailable",
            "type": "ServiceUnavailable",
            "details": e.details
        })
    
    except ValidationException as e:
        logger.warning(f"Chat validation error: {e.message}")
        raise HTTPException(status_code=400, detail={
            "error": e.message,
            "type": "ValidationError",
            "details": e.details
        })
    
    except Exception as e:
        logger.error(f"Unexpected error in chat processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": "Internal server error processing your question",
            "type": "InternalServerError"
        })


@router.post("/validate-chart", response_model=dict)
async def validate_chart_specification(
    chart_spec_data: dict,
    file_id: str,
    csv_service: CSVService = Depends(get_csv_service),
    chart_service: ChartService = Depends(get_chart_service),
    file_storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Validate chart specification against CSV data.
    
    Similar to a validation action in .NET Web API.
    Used for testing and debugging chart specifications.
    """
    logger.info(f"Chart validation request: file_id={file_id}")
    
    try:
        # Get file and metadata
        file_path = await file_storage.get_file_path(file_id)
        csv_metadata = await csv_service.get_csv_metadata(file_path, file_id)
        
        # Parse and validate chart specification
        chart_spec = ChartSpec(**chart_spec_data)
        validation_result = await chart_service.validate_chart_spec(chart_spec, csv_metadata)
        
        return JSONResponse({
            "is_valid": validation_result.is_valid,
            "error_message": validation_result.error_message,
            "suggestions": validation_result.suggestions,
            "chart_spec": chart_spec.dict()
        })
        
    except FileProcessingException:
        raise HTTPException(status_code=404, detail={
            "error": f"CSV file not found: {file_id}",
            "type": "FileNotFound"
        })
    
    except Exception as e:
        logger.error(f"Chart validation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": "Error validating chart specification",
            "type": "InternalServerError"
        })


def _generate_suggested_questions(csv_metadata) -> list[str]:
    """
    Generate contextual suggested questions based on CSV data.
    Similar to helper methods in .NET controllers.
    """
    suggestions = []
    
    numeric_cols = csv_metadata.get_numeric_columns()
    categorical_cols = csv_metadata.get_categorical_columns()
    datetime_cols = csv_metadata.get_datetime_columns()
    
    # Time-based suggestions
    if datetime_cols and numeric_cols:
        suggestions.append(f"Show {numeric_cols[0]} trends over time")
        suggestions.append(f"Compare {numeric_cols[0]} by month")
    
    # Categorical breakdown suggestions
    if categorical_cols and numeric_cols:
        suggestions.append(f"Show {numeric_cols[0]} by {categorical_cols[0]}")
        suggestions.append(f"Compare {numeric_cols[0]} across {categorical_cols[0]}")
    
    # Correlation suggestions
    if len(numeric_cols) >= 2:
        suggestions.append(f"Show relationship between {numeric_cols[0]} and {numeric_cols[1]}")
    
    # Summary suggestions
    if numeric_cols:
        suggestions.append(f"Show total {numeric_cols[0]}")
        suggestions.append(f"Show average {numeric_cols[0]}")
    
    # Fallback suggestions
    if not suggestions:
        suggestions = [
            "Show me a summary of the data",
            "Create a bar chart",
            "Show trends over time",
            "Compare categories"
        ]
    
    return suggestions[:4]  # Limit to 4 suggestions