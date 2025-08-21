"""
Chart Models - Data structures that define how charts should be created

This file contains Pydantic models that define the structure of chart
specifications and related data. These models serve as contracts between
different parts of our application and ensure type safety.

Key Concepts:
1. Pydantic BaseModel: Provides automatic validation, serialization, and type checking
2. Field() definitions: Specify validation rules and documentation
3. Validators: Custom logic to ensure data integrity
4. Type hints: Ensure compile-time type safety

Think of these as "blueprints" that define exactly what data is required
and allowed for different chart operations.
"""

from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class CalculationSpec(BaseModel):
    """
    Model for calculated/derived fields
    
    This defines how to create new columns from existing data.
    For example: revenue = units_sold * unit_price
    
    When users ask for "revenue by region" but the CSV only has
    units_sold and unit_price columns, this specification tells
    the system how to calculate the revenue field.
    """
    
    field_name: str = Field(
        ...,  # ... means required field
        description="Name of the calculated field (e.g., 'revenue')"
    )
    
    formula: str = Field(
        ..., 
        description="Mathematical formula using existing columns (e.g., 'units_sold * unit_price')"
    )
    
    description: str = Field(
        ..., 
        description="Human-readable description of what this calculation does"
    )


class FilterSpec(BaseModel):
    """
    Model for data filtering specifications
    
    This defines how to filter data before creating charts.
    For example: "only show data from 2024" or "exclude region = 'test'"
    
    Supports various operators for different types of filtering needs.
    """
    
    column: str = Field(
        ..., 
        description="Name of the column to filter on"
    )
    
    # Literal type restricts values to only these specific strings
    operator: Literal["==", "!=", ">", ">=", "<", "<=", "in", "not_in"] = Field(
        ..., 
        description="Filter operator - how to compare the column value"
    )
    
    # Union type means the value can be any of these types
    value: Union[str, int, float, List[Union[str, int, float]]] = Field(
        ..., 
        description="Value(s) to compare against - single value or list for 'in'/'not_in'"
    )


class ChartSpec(BaseModel):
    """
    Main chart specification model
    
    This is the core model that defines everything needed to create a chart.
    It's what the LLM service generates from natural language questions,
    and what the chart service uses to process data.
    
    Example: User asks "show sales by region"
    -> LLM creates: ChartSpec(chart_type="bar", x="region", y="sales", aggregation="sum")
    -> Chart service uses this to create the actual chart data
    """
    
    # Chart type is restricted to only these supported types
    chart_type: Literal["bar", "line", "scatter", "pie"] = Field(
        ..., 
        description="Type of chart to generate - determines visualization style"
    )
    
    x: Optional[str] = Field(
        None, 
        description="Column name for x-axis (horizontal axis) - usually categories"
    )
    
    y: Optional[str] = Field(
        None, 
        description="Column name for y-axis (vertical axis) - usually numeric values"
    )
    
    # Optional with default value
    aggregation: Optional[Literal["sum", "mean", "count", "min", "max", "none"]] = Field(
        "none", 
        description="How to combine multiple rows of data (e.g., sum sales by region)"
    )
    
    # Optional list of strings for multi-dimensional grouping
    group_by: Optional[List[str]] = Field(
        None, 
        description="Additional columns to group by for multi-dimensional charts"
    )
    
    calculation: Optional[CalculationSpec] = Field(
        None, 
        description="Specification for calculated fields (like revenue calculation)"
    )
    
    filters: Optional[List[FilterSpec]] = Field(
        None, 
        description="List of filters to apply to the data before charting"
    )
    
    explanation: Optional[str] = Field(
        None, 
        description="Human-readable explanation of what this chart shows"
    )
    
    title: Optional[str] = Field(
        None, 
        description="Title to display on the chart"
    )
    
    @field_validator('group_by')
    @classmethod
    def validate_group_by_limit(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """
        Custom validator for group_by field
        
        This limits the number of grouping dimensions to prevent overly complex
        charts that would be unreadable. We limit to 3 dimensions max.
        
        @field_validator decorator tells Pydantic to run this function
        whenever the group_by field is set.
        """
        if v and len(v) > 3:
            # Instead of raising an error, we just truncate to first 3
            # This is more user-friendly than rejecting the request
            v = v[:3]
        return v
    
    @model_validator(mode='after')
    def set_defaults_and_validate(self) -> 'ChartSpec':
        """
        Model-level validator that runs after all fields are processed
        
        This sets intelligent defaults and performs cross-field validation.
        It runs after individual field validation is complete.
        
        The 'after' mode means this validator receives the complete model
        instance and can modify multiple fields at once.
        """
        # Set intelligent default explanation if none provided
        if not self.explanation:
            self.explanation = f"{self.chart_type.title()} chart"
            if self.x and self.y:
                # Create more descriptive explanation when we have both axes
                self.explanation = f"{self.chart_type.title()} chart of {self.y} by {self.x}"
        
        # Set default title to match explanation
        if not self.title:
            self.title = self.explanation
        
        # Ensure charts that need aggregation have it set
        if self.chart_type in ["bar", "line", "scatter"] and not self.y:
            if self.aggregation == "none":
                # Default to sum for numeric aggregations
                self.aggregation = "sum"
        
        return self  # Must return the modified instance


class ChartData(BaseModel):
    """Generated chart data ready for frontend visualization."""
    
    chart_spec: ChartSpec = Field(..., description="Original chart specification")
    data: List[Dict[str, Any]] = Field(..., description="Processed data for visualization")
    summary_stats: Dict[str, Any] = Field(
        default_factory=dict, description="Summary statistics about the data"
    )
    data_transformations: List[str] = Field(
        default_factory=list, description="List of transformations applied to data"
    )


class ChartValidationResult(BaseModel):
    """Result of chart specification validation."""
    
    is_valid: bool = Field(..., description="Whether chart spec is valid")
    error_message: Optional[str] = Field(None, description="Error message if invalid")
    suggestions: List[str] = Field(
        default_factory=list, description="Suggestions for fixing invalid spec"
    )
    
    @classmethod
    def success(cls) -> "ChartValidationResult":
        """Create successful validation result."""
        return cls(is_valid=True)
    
    @classmethod
    def failure(cls, error_message: str, suggestions: List[str] = None) -> "ChartValidationResult":
        """Create failed validation result."""
        return cls(
            is_valid=False, 
            error_message=error_message,
            suggestions=suggestions or []
        )