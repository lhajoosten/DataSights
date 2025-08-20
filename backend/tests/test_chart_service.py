"""
Chart Service tests focusing on business logic.
Following .NET service layer testing patterns.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, AsyncMock

from app.services.chart_service import ChartService
from app.models.chart_models import ChartSpec, ChartData
from app.models.csv_models import CSVMetadata
from app.core.exceptions import ValidationException


class TestChartService:
    """Chart service test class with comprehensive scenarios."""
    
    @pytest.fixture
    def chart_service(self):
        return ChartService()
    
    @pytest.fixture
    def sample_dataframe(self):
        """Sample dataframe for chart testing."""
        return pd.DataFrame({
            'region': ['North', 'South', 'East', 'West', 'North', 'South'],
            'product': ['A', 'A', 'B', 'B', 'B', 'A'],
            'units_sold': [10, 15, 12, 20, 8, 25],
            'unit_price': [10.0, 10.0, 15.0, 15.0, 15.0, 10.0],
            'date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', '2024-01-06'])
        })
    
    @pytest.fixture
    def csv_metadata(self):
        """Mock CSV metadata."""
        return Mock(spec=CSVMetadata)
    
    async def test_generate_simple_bar_chart(self, chart_service, sample_dataframe, csv_metadata):
        """Test simple bar chart generation - core functionality."""
        # Arrange
        chart_spec = ChartSpec(
            chart_type="bar",
            group_by=None,
            calculation=None,
            filters=None,
            explanation="Total sales by region",
            title="Sales by Region",
            x="region",
            y="units_sold",
            aggregation="sum"
        )
        
        # Act
        result = await chart_service.generate_chart_data(chart_spec, sample_dataframe, csv_metadata)
        
        # Assert
        assert isinstance(result, ChartData)
        assert result.chart_spec.chart_type == "bar"
        assert len(result.data) > 0
        assert result.summary_stats["total_records"] > 0
        
        # Verify aggregation worked
        regions_in_data = [point["region"] for point in result.data]
        assert "North" in regions_in_data
        assert "South" in regions_in_data
    
    async def test_generate_grouped_chart(self, chart_service, sample_dataframe, csv_metadata):
        """Test multi-dimensional grouped chart - complex scenario."""
        # Arrange
        chart_spec = ChartSpec(
            chart_type="bar",
            calculation=None,
            filters=None,
            explanation="Total sales by region",
            title="Sales by Region",
            x="region",
            y="units_sold",
            aggregation="sum",
            group_by=["product"]
        )
        
        # Act
        result = await chart_service.generate_chart_data(chart_spec, sample_dataframe, csv_metadata)
        
        # Assert
        assert isinstance(result, ChartData)
        assert len(result.data) > 0
        
        # ChartService returns grouped rows with 'product' and 'region' columns, not pivoted product columns
        assert all("region" in dp and "product" in dp for dp in result.data)
        # Ensure we have rows for both products A and B
        products = {dp.get("product") for dp in result.data}
        assert "A" in products and "B" in products
    
    async def test_revenue_calculation(self, chart_service, sample_dataframe, csv_metadata):
        """Test calculated field functionality - business logic."""
        # Arrange
        chart_spec = ChartSpec(
            chart_type="bar",
            calculation=None,
            filters=None,
            group_by=None,
            explanation="Total revenue by region",
            title="Revenue by Region",
            x="region",
            y="revenue",  # This should trigger revenue calculation
            aggregation="sum"
        )
        
        # Act
        result = await chart_service.generate_chart_data(chart_spec, sample_dataframe, csv_metadata)
        
        # Assert
        assert isinstance(result, ChartData)
        assert "Calculated revenue" in str(result.data_transformations)
        
        # Verify revenue calculation
        for point in result.data:
            if "revenue" in point:
                assert point["revenue"] is not None
    
    async def test_empty_dataframe_handling(self, chart_service, csv_metadata):
        """Test empty data handling - edge case."""
        # Arrange
        empty_df = pd.DataFrame()
        chart_spec = ChartSpec(chart_type="bar", x="region", y="sales")
        
        # Act
        result = await chart_service.generate_chart_data(chart_spec, empty_df, csv_metadata)
        
        # Assert
        assert isinstance(result, ChartData)
        assert len(result.data) == 0
        assert result.summary_stats["total_records"] == 0
    
    def test_determine_grouping_columns(self, chart_service, sample_dataframe):
        """Test grouping logic - unit test for specific method."""
        # Arrange
        chart_spec = ChartSpec(
            chart_type="bar",
            calculation=None,
            filters=None,
            explanation="Total sales by region",
            title="Sales by Region",
            aggregation="sum",
            x="region",
            y="units_sold",
            group_by=["product"]
        )
        
        # Act
        group_cols = chart_service._determine_grouping_columns(chart_spec, sample_dataframe)
        
        # Assert
        assert "product" in group_cols
        assert "region" in group_cols
        assert len(group_cols) == 2