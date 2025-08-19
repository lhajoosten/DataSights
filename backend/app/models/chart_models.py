"""
Chart specification and generation models with calculated field support.
"""

from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class CalculationSpec(BaseModel):
    """Specification for calculated/derived fields."""
    
    field_name: str = Field(..., description="Name of the calculated field")
    formula: str = Field(..., description="Mathematical formula using existing columns")
    description: str = Field(..., description="Human-readable description of calculation")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "field_name": "revenue",
                "formula": "units_sold * unit_price",
                "description": "Revenue calculated as units sold times unit price"
            }
        }
    }


class FilterSpec(BaseModel):
    """Specification for data filtering."""
    
    column: str = Field(..., description="Column name to filter on")
    operator: Literal["==", "!=", ">", ">=", "<", "<=", "in", "not_in"] = Field(
        ..., description="Filter operator"
    )
    value: Union[str, int, float, List[Union[str, int, float]]] = Field(
        ..., description="Filter value(s)"
    )
    
    @field_validator('value')
    @classmethod
    def validate_value_for_operator(cls, v: Any, info) -> Any:
        """Validate that value type matches operator."""
        # Get the operator from the model data
        data = info.data if hasattr(info, 'data') else {}
        op = data.get('operator')
        
        if op in ['in', 'not_in'] and not isinstance(v, list):
            raise ValueError(f"Operator '{op}' requires a list value")
        elif op not in ['in', 'not_in'] and isinstance(v, list):
            raise ValueError(f"Operator '{op}' cannot use a list value")
        return v


class ChartSpec(BaseModel):
    """
    Enhanced chart specification with calculated field support.
    This is the core contract between LLM and chart generation.
    """
    
    chart_type: Literal["bar", "line", "scatter", "pie"] = Field(
        ..., description="Type of chart to generate"
    )
    x: Optional[str] = Field(None, description="Column name for x-axis (can be calculated field)")
    y: Optional[str] = Field(None, description="Column name for y-axis (can be calculated field)")
    aggregation: Optional[Literal["sum", "mean", "count", "min", "max", "none"]] = Field(
        "none", description="Aggregation function to apply"
    )
    group_by: Optional[List[str]] = Field(
        None, description="Columns to group by (max 3 for readability)"
    )
    calculation: Optional[CalculationSpec] = Field(
        None, description="Calculated field specification"
    )
    filters: Optional[List[FilterSpec]] = Field(
        None, description="Data filters to apply"
    )
    explanation: str = Field(
        ..., description="Human-readable explanation of the chart"
    )
    title: Optional[str] = Field(None, description="Chart title")
    
    @field_validator('group_by')
    @classmethod
    def validate_group_by_limit(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Limit group_by to maximum 3 columns for readability."""
        if v and len(v) > 3:
            raise ValueError("Maximum 3 group_by columns allowed for chart readability")
        return v
    
    @model_validator(mode='after')
    def validate_chart_requirements(self) -> 'ChartSpec':
        """Validate chart type requirements."""
        chart_type = self.chart_type
        
        if chart_type == "pie":
            if not self.x:
                raise ValueError("Pie charts require an x-axis column for categories")
            if not self.y:
                raise ValueError("Pie charts require a y-axis column for values")
        
        elif chart_type == "scatter":
            if not self.x:
                raise ValueError("Scatter plots require an x-axis column")
            if not self.y:
                raise ValueError("Scatter plots require a y-axis column")
        
        elif chart_type in ["bar", "line"]:
            if not self.y and self.aggregation == "none":
                raise ValueError(
                    f"{chart_type.title()} charts require a y-axis column or aggregation"
                )
        
        return self
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "chart_type": "bar",
                "x": "month",
                "y": "revenue",
                "aggregation": "sum",
                "group_by": ["region"],
                "calculation": {
                    "field_name": "revenue",
                    "formula": "units_sold * unit_price",
                    "description": "Revenue calculated as units sold times unit price"
                },
                "filters": [
                    {
                        "column": "year",
                        "operator": "==",
                        "value": 2024
                    }
                ],
                "explanation": "Bar chart showing total revenue by month, grouped by region",
                "title": "Monthly Revenue by Region"
            }
        }
    }


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
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "chart_spec": {
                    "chart_type": "bar",
                    "x": "month",
                    "y": "revenue",
                    "aggregation": "sum",
                    "explanation": "Monthly revenue totals",
                    "calculation": {
                        "field_name": "revenue",
                        "formula": "units_sold * unit_price",
                        "description": "Calculated revenue"
                    }
                },
                "data": [
                    {"month": "Jan", "revenue": 1000},
                    {"month": "Feb", "revenue": 1200}
                ],
                "summary_stats": {
                    "total_records": 2,
                    "revenue_total": 2200
                },
                "data_transformations": [
                    "Calculated revenue = units_sold * unit_price",
                    "Grouped by month",
                    "Aggregated revenue using sum"
                ]
            }
        }
    }


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