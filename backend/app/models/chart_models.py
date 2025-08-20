"""
Chart specification and generation models - fixed validation.
"""

from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class CalculationSpec(BaseModel):
    """Specification for calculated/derived fields."""
    
    field_name: str = Field(..., description="Name of the calculated field")
    formula: str = Field(..., description="Mathematical formula using existing columns")
    description: str = Field(..., description="Human-readable description of calculation")


class FilterSpec(BaseModel):
    """Specification for data filtering."""
    
    column: str = Field(..., description="Column name to filter on")
    operator: Literal["==", "!=", ">", ">=", "<", "<=", "in", "not_in"] = Field(
        ..., description="Filter operator"
    )
    value: Union[str, int, float, List[Union[str, int, float]]] = Field(
        ..., description="Filter value(s)"
    )


class ChartSpec(BaseModel):
    """
    Simple chart specification - fixed validation issues.
    """
    
    chart_type: Literal["bar", "line", "scatter", "pie"] = Field(
        ..., description="Type of chart to generate"
    )
    x: Optional[str] = Field(None, description="Column name for x-axis")
    y: Optional[str] = Field(None, description="Column name for y-axis")
    aggregation: Optional[Literal["sum", "mean", "count", "min", "max", "none"]] = Field(
        "none", description="Aggregation function to apply"
    )
    group_by: Optional[List[str]] = Field(
        None, description="Columns to group by"
    )
    calculation: Optional[CalculationSpec] = Field(
        None, description="Calculated field specification"
    )
    filters: Optional[List[FilterSpec]] = Field(
        None, description="Data filters to apply"
    )
    explanation: Optional[str] = Field(
        None, description="Human-readable explanation of the chart"
    )
    title: Optional[str] = Field(None, description="Chart title")
    
    @field_validator('group_by')
    @classmethod
    def validate_group_by_limit(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Limit group_by to maximum 3 columns for readability."""
        if v and len(v) > 3:
            v = v[:3]  # Truncate instead of failing
        return v
    
    @model_validator(mode='after')
    def set_defaults_and_validate(self) -> 'ChartSpec':
        """Set sensible defaults and validate."""
        # Set default explanation if missing
        if not self.explanation:
            self.explanation = f"{self.chart_type.title()} chart"
            if self.x and self.y:
                self.explanation = f"{self.chart_type.title()} chart of {self.y} by {self.x}"
        
        # Set default title if missing
        if not self.title:
            self.title = self.explanation
        
        # Basic validation for chart requirements
        if self.chart_type in ["bar", "line", "scatter"] and not self.y:
            if self.aggregation == "none":
                self.aggregation = "sum"  # Default aggregation
        
        return self


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