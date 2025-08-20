"""
LLM Service comprehensive tests following .NET testing patterns.
Critical for ensuring reliable AI functionality.
"""

import pytest
import json
from unittest.mock import AsyncMock, Mock, patch
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from app.models.chat_models import ChatMessage

from app.services.llm_service import LLMService
from app.models.csv_models import CSVMetadata
from app.core.exceptions import LLMServiceException
from app.core.config import Settings


class TestLLMService:
    """LLM Service test class with comprehensive AI interaction scenarios."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.openai_api_key = "test-api-key"
        settings.openai_model = "gpt-4"
        settings.max_tokens = 1000
        settings.temperature = 0.1
        return settings

    @pytest.fixture
    def llm_service(self, mock_settings):
        """LLM service with mocked dependencies."""
        service = LLMService()
        # inject mocked settings and a dummy client to be patched in tests
        service.settings = mock_settings
        service.client = None
        return service
    
    @pytest.fixture
    def sample_csv_metadata(self):
        """Sample CSV metadata for testing."""
        metadata = Mock(spec=CSVMetadata)
        metadata.filename = "sales_data.csv"
        metadata.columns = ["date", "region", "product", "units_sold", "unit_price"]
        metadata.column_types = {
            "date": "datetime",
            "region": "categorical", 
            "product": "categorical",
            "units_sold": "numeric",
            "unit_price": "numeric"
        }
        metadata.get_numeric_columns.return_value = ["units_sold", "unit_price"]
        metadata.get_categorical_columns.return_value = ["region", "product"]
        metadata.get_datetime_columns.return_value = ["date"]
        metadata.row_count = 1000
        return metadata
    
    @pytest.fixture
    def valid_llm_response(self):
        """Valid LLM response structure."""
        return {
            "explanation": "This bar chart shows total sales by region, aggregated to provide insights into regional performance.",
            "chart_spec": {
                "chart_type": "bar",
                "x": "region",
                "y": "units_sold", 
                "aggregation": "sum",
                "group_by": None,
                "filter_conditions": None
            }
        }
    
    async def test_generate_chart_response_success(self, llm_service, sample_csv_metadata, valid_llm_response):
        """Test successful LLM chart generation - happy path."""
        # Arrange
        question = "Show total sales by region"
        context = []
        
        # Mock OpenAI response
        mock_completion = Mock(spec=ChatCompletion)
        mock_choice = Mock(spec=Choice)
        mock_message = Mock(spec=ChatCompletionMessage)
        mock_message.content = json.dumps(valid_llm_response)
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        with patch.object(llm_service, 'client') as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

            # Act
            result = await llm_service.generate_chart_spec(question, sample_csv_metadata, context)

            # Assert - result is an LLMResponse
            assert result.content == valid_llm_response["explanation"]
            assert result.chart_spec["chart_type"] == "bar"
            assert result.chart_spec["x"] == "region"
            assert result.chart_spec["y"] == "units_sold"

            # Verify OpenAI was called with correct parameters
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-4"
            assert call_args[1]["temperature"] == 0.1
    
    async def test_generate_chart_response_with_context(self, llm_service, sample_csv_metadata, valid_llm_response):
        """Test LLM with chat context - conversation memory."""
        # Arrange
        question = "Show it broken down by product too"
        context = [
            ChatMessage(role="user", content="Show total sales by region", timestamp="2025-01-01T00:00:00Z"),
            ChatMessage(role="assistant", content="Here's a bar chart of sales by region", timestamp="2025-01-01T00:00:01Z")
        ]
        
        mock_completion = Mock(spec=ChatCompletion)
        mock_choice = Mock(spec=Choice)
        mock_message = Mock(spec=ChatCompletionMessage)
        
        # Updated response for follow-up question
        follow_up_response = {
            **valid_llm_response,
            "chart_spec": {
                **valid_llm_response["chart_spec"],
                "group_by": ["product"]
            }
        }
        mock_message.content = json.dumps(follow_up_response)
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        with patch.object(llm_service, 'client') as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

            # Act
            result = await llm_service.generate_chart_spec(question, sample_csv_metadata, context)

            # Assert
            assert result.chart_spec["group_by"] == ["product"]

            # Verify context was included in the prompt
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]["messages"]

            # Should include system prompt + user prompt + context messages
            assert len(messages) >= 4  # system + user + 2 context
            assert any("Show it broken down by product too" in str(m.get("content", "")) for m in messages)
    
    async def test_generate_chart_response_malformed_json(self, llm_service, sample_csv_metadata):
        """Test handling of malformed LLM response - error recovery."""
        # Arrange
        question = "Show sales data"
        
        mock_completion = Mock(spec=ChatCompletion)
        mock_choice = Mock(spec=Choice)
        mock_message = Mock(spec=ChatCompletionMessage)
        mock_message.content = "Invalid JSON response from LLM"
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        with patch.object(llm_service, 'client') as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

            # Act
            result = await llm_service.generate_chart_spec(question, sample_csv_metadata, [])

            # Assert - malformed JSON returns a clarification LLMResponse (no exception)
            assert result.requires_clarification is True
            assert result.clarification_question is not None
    
    async def test_generate_chart_response_api_error(self, llm_service, sample_csv_metadata):
        """Test OpenAI API error handling - service reliability."""
        # Arrange
        question = "Show sales data"
        with patch.object(llm_service, 'client') as mock_client:
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API rate limit exceeded"))

            # Act
            result = await llm_service.generate_chart_spec(question, sample_csv_metadata, [])

            # Assert - service returns an error LLMResponse rather than raising
            assert result.requires_clarification is True
            assert "sorry" in result.content.lower() or (result.clarification_question and "error" in result.clarification_question.lower())
    
    async def test_fallback_mode_no_api_key(self, sample_csv_metadata):
        """Test fallback mode when no API key provided - graceful degradation."""
        # Arrange
        settings = Mock(spec=Settings)
        settings.openai_api_key = ""  # No API key
        service = LLMService()
        service.settings = settings
        service.client = None

        question = "Show total sales by region"

        # Act
        result = await service.generate_chart_spec(question, sample_csv_metadata, [])

        # Assert - fallback response should provide a chart_spec dict
        assert result.requires_clarification is False
        assert "units" in result.content.lower() or "sales" in result.content.lower()
        assert result.chart_spec["chart_type"] in ["bar", "line"]
        assert result.chart_spec["x"] is not None
        assert result.chart_spec["y"] is not None
    
    async def test_revenue_calculation_detection(self, llm_service, sample_csv_metadata, valid_llm_response):
        """Test revenue calculation prompt enhancement - business logic."""
        # Arrange
        question = "Show revenue by region"
        
        # Response should trigger revenue calculation
        revenue_response = {
            **valid_llm_response,
            "chart_spec": {
                **valid_llm_response["chart_spec"],
                "y": "revenue"  # This should trigger calculated field
            }
        }
        
        mock_completion = Mock(spec=ChatCompletion)
        mock_choice = Mock(spec=Choice)
        mock_message = Mock(spec=ChatCompletionMessage)
        mock_message.content = json.dumps(revenue_response)
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        with patch.object(llm_service, 'client') as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

            # Act
            result = await llm_service.generate_chart_spec(question, sample_csv_metadata, [])

            # Assert
            assert result.chart_spec["y"] == "revenue"

            # Verify prompt included revenue calculation context
            call_args = mock_client.chat.completions.create.call_args
            prompt_content = str(call_args[1]["messages"])
            assert "revenue" in prompt_content.lower()
            assert "units_sold * unit_price" in prompt_content
    
    def test_build_system_prompt(self, llm_service, sample_csv_metadata):
        """Test system prompt construction - prompt engineering."""
        # Act
        prompt = llm_service._build_system_prompt(sample_csv_metadata)
        
        # Assert
        # Prompt should contain dataset columns and guidance
        assert str(sample_csv_metadata.columns) in prompt
        assert "date" in prompt
        assert "region" in prompt
        assert "units_sold" in prompt
        assert "bar" in prompt  # Should mention chart types
        assert "RESPOND WITH JSON" in prompt.upper() or "RESPOND WITH JSON:" in prompt
        assert "units_sold * unit_price" in prompt  # Calculated fields
    
    def test_parse_llm_response_success(self, llm_service, valid_llm_response):
        """Test successful response parsing - data validation."""
        # Arrange
        response_text = json.dumps(valid_llm_response)
        # Act
        result = llm_service._parse_openai_response(response_text)

        # Assert - returns LLMResponse
        assert result.content == valid_llm_response["explanation"]
        assert result.chart_spec["chart_type"] == "bar"
    
    def test_parse_llm_response_missing_fields(self, llm_service):
        """Test response validation with missing required fields."""
        # Arrange
        incomplete_response = {
            "explanation": "Chart explanation",
            # Missing chart_spec
        }
        response_text = json.dumps(incomplete_response)
        
        # Act & Assert
        result = llm_service._parse_openai_response(response_text)
        assert result.requires_clarification is True