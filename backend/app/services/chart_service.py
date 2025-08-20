"""
Simplified chart generation service focused on reliability.
This service handles basic chart data processing with minimal complexity.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
import warnings

from app.models.chart_models import ChartSpec, ChartData, ChartValidationResult, FilterSpec, CalculationSpec
from app.models.csv_models import CSVMetadata
from app.core.exceptions import ValidationException, FileProcessingException

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)


class ChartService:
    """Simple, reliable chart data generation service."""
    
    def __init__(self):
        self.max_data_points = 1000
        self.max_categories = 50
    
    async def generate_chart_data(
        self, 
        chart_spec: ChartSpec, 
        dataframe: pd.DataFrame,
        csv_metadata: CSVMetadata
    ) -> ChartData:
        """Generate chart data with simple, reliable processing."""
        try:
            logger.info(f"Generating chart: {chart_spec.chart_type}, X: {chart_spec.x}, Y: {chart_spec.y}")
            logger.info(f"Input data shape: {dataframe.shape}")
            
            # Start with clean copy
            df = dataframe.copy()
            transformations = []
            
            # Step 1: Apply calculated fields
            if chart_spec.calculation:
                df, calc_transformations = self._apply_calculated_field(df, chart_spec.calculation)
                transformations.extend(calc_transformations)
                logger.info(f"After calculation, data shape: {df.shape}")
            
            # Step 2: Handle time grouping
            if chart_spec.x and 'month' in chart_spec.x.lower():
                df, time_transformations = self._extract_month_from_date(df)
                transformations.extend(time_transformations)
                logger.info(f"After time extraction, data shape: {df.shape}")
            
            # Step 3: Apply filters (simple approach)
            if chart_spec.filters:
                df, filter_transformations = self._apply_simple_filters(df, chart_spec.filters)
                transformations.extend(filter_transformations)
                logger.info(f"After filters, data shape: {df.shape}")
            
            # Step 4: Simple aggregation
            if chart_spec.aggregation != "none" or chart_spec.group_by:
                df, agg_transformations = self._apply_simple_aggregation(df, chart_spec)
                transformations.extend(agg_transformations)
                logger.info(f"After aggregation, data shape: {df.shape}")
            
            # Step 5: Validate we have data
            if df.empty:
                logger.warning("DataFrame is empty after processing")
                return ChartData(
                    chart_spec=chart_spec,
                    data=[],
                    summary_stats={"total_records": 0, "error": "No data after processing"},
                    data_transformations=transformations
                )
            
            # Step 6: Format for frontend
            chart_data = self._format_chart_data(chart_spec, df)
            logger.info(f"Generated {len(chart_data)} data points")
            
            # Step 7: Calculate summary stats
            summary_stats = self._calculate_summary_stats(df, chart_spec)
            
            return ChartData(
                chart_spec=chart_spec,
                data=chart_data,
                summary_stats=summary_stats,
                data_transformations=transformations
            )
            
        except Exception as e:
            logger.error(f"Chart generation error: {str(e)}", exc_info=True)
            raise FileProcessingException(f"Failed to generate chart: {str(e)}")
    
    def _apply_calculated_field(self, df: pd.DataFrame, calculation: CalculationSpec) -> Tuple[pd.DataFrame, List[str]]:
        """Simple calculated field application."""
        try:
            formula = calculation.formula
            field_name = calculation.field_name
            
            logger.info(f"Applying calculation: {field_name} = {formula}")
            
            # Simple formula parsing - look for column names
            columns_in_formula = []
            for col in df.columns:
                if col in formula:
                    columns_in_formula.append(col)
            
            logger.info(f"Found columns in formula: {columns_in_formula}")
            
            # Convert to numeric
            for col in columns_in_formula:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Simple evaluation (for basic math operations)
            if '*' in formula and len(columns_in_formula) == 2:
                # Simple multiplication: col1 * col2
                col1, col2 = columns_in_formula[0], columns_in_formula[1]
                df[field_name] = df[col1] * df[col2]
            else:
                # Fallback for other operations
                safe_formula = formula
                for col in columns_in_formula:
                    safe_formula = safe_formula.replace(col, f"df['{col}']")
                
                # Evaluate safely
                result = eval(safe_formula)
                df[field_name] = result
            
            # Remove NaN values
            df[field_name] = df[field_name].fillna(0)
            
            transformations = [
                f"Calculated {field_name} = {formula}",
                f"Description: {calculation.description}"
            ]
            
            logger.info(f"Calculation successful. Sample values: {df[field_name].head(3).tolist()}")
            return df, transformations
            
        except Exception as e:
            logger.error(f"Calculation failed: {str(e)}")
            # Don't fail completely - just skip calculation
            return df, [f"Calculation failed: {str(e)}"]
    
    def _extract_month_from_date(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Simple month extraction from date column."""
        transformations = []
        
        # Find date column
        date_col = None
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    # Try to parse a few values as dates
                    sample = df[col].dropna().head(5)
                    pd.to_datetime(sample, errors='raise')
                    date_col = col
                    break
                except:
                    continue
        
        if date_col:
            try:
                # Convert to datetime and extract month
                df['month'] = pd.to_datetime(df[date_col]).dt.to_period('M').astype(str)
                transformations.append(f"Extracted month from {date_col}")
                logger.info(f"Month extraction successful from {date_col}")
            except Exception as e:
                logger.warning(f"Month extraction failed: {str(e)}")
        else:
            logger.warning("No date column found for month extraction")
        
        return df, transformations
    
    def _apply_simple_filters(self, df: pd.DataFrame, filters: List[FilterSpec]) -> Tuple[pd.DataFrame, List[str]]:
        """Simple filter application."""
        transformations = []
        
        for filter_spec in filters:
            col = filter_spec.column
            op = filter_spec.operator
            value = filter_spec.value
            
            if col not in df.columns:
                logger.warning(f"Filter column '{col}' not found in data")
                continue
            
            try:
                initial_rows = len(df)
                
                if op == "==":
                    df = df[df[col] == value]
                elif op == "!=":
                    df = df[df[col] != value]
                elif op == ">":
                    df = df[pd.to_numeric(df[col], errors='coerce') > float(value)]
                elif op == ">=":
                    df = df[pd.to_numeric(df[col], errors='coerce') >= float(value)]
                elif op == "<":
                    df = df[pd.to_numeric(df[col], errors='coerce') < float(value)]
                elif op == "<=":
                    df = df[pd.to_numeric(df[col], errors='coerce') <= float(value)]
                elif op == "in":
                    df = df[df[col].isin(value)]
                elif op == "not_in":
                    df = df[~df[col].isin(value)]
                
                final_rows = len(df)
                transformations.append(f"Filtered {col} {op} {value} ({initial_rows} → {final_rows} rows)")
                
            except Exception as e:
                logger.warning(f"Filter failed {col} {op} {value}: {str(e)}")
                continue
        
        return df, transformations
    
    def _apply_simple_aggregation(self, df: pd.DataFrame, chart_spec: ChartSpec) -> Tuple[pd.DataFrame, List[str]]:
        """Simple aggregation logic."""
        transformations = []
        
        if chart_spec.aggregation == "none" and not chart_spec.group_by:
            return df, transformations
        
        # Determine grouping columns
        group_cols = []
        if chart_spec.group_by:
            group_cols.extend(chart_spec.group_by)
        if chart_spec.x and chart_spec.x not in group_cols and chart_spec.x in df.columns:
            group_cols.append(chart_spec.x)
        
        # Filter out columns that don't exist
        group_cols = [col for col in group_cols if col in df.columns]
        
        if not group_cols:
            logger.warning("No valid grouping columns found")
            return df, transformations
        
        try:
            logger.info(f"Grouping by: {group_cols}")
            
            if chart_spec.aggregation == "count":
                # Count rows
                agg_df = df.groupby(group_cols).size().reset_index(name='count')
                if not chart_spec.y:
                    chart_spec.y = 'count'
                transformations.append(f"Grouped by {group_cols} and counted rows")
                
            elif chart_spec.y and chart_spec.y in df.columns:
                # Aggregate specific column
                agg_key = chart_spec.aggregation if chart_spec.aggregation else "sum"
                agg_func = {
                    "sum": "sum",
                    "mean": "mean",
                    "min": "min",
                    "max": "max"
                }.get(agg_key, "sum")
                
                # Convert to numeric
                df[chart_spec.y] = pd.to_numeric(df[chart_spec.y], errors='coerce')
                
                # Group and aggregate
                agg_df = df.groupby(group_cols)[chart_spec.y].agg(agg_func).reset_index()
                transformations.append(f"Grouped by {group_cols} and applied {agg_func} to {chart_spec.y}")
            
            else:
                logger.warning(f"Y column '{chart_spec.y}' not found for aggregation")
                return df, transformations
            
            logger.info(f"Aggregation result shape: {agg_df.shape}")
            return agg_df, transformations
            
        except Exception as e:
            logger.error(f"Aggregation failed: {str(e)}")
            return df, transformations
    
    def _format_chart_data(self, chart_spec: ChartSpec, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Simple data formatting for charts."""
        data = []
        
        logger.info(f"Formatting {len(df)} rows for chart")
        logger.info(f"Available columns: {list(df.columns)}")
        
        for _, row in df.iterrows():
            point = {}
            
            # Add all columns to be safe
            for col in df.columns:
                value = row[col]
                # Convert to JSON-safe types
                if pd.isna(value):
                    point[col] = None
                elif isinstance(value, (np.integer, np.int64)):
                    point[col] = int(value)
                elif isinstance(value, (np.floating, np.float64)):
                    point[col] = float(value)
                elif isinstance(value, pd.Timestamp):
                    point[col] = value.isoformat()
                else:
                    point[col] = str(value)
            
            data.append(point)
        
        logger.info(f"Formatted {len(data)} data points")
        if data:
            logger.info(f"Sample data point: {data[0]}")
        
        return data
    
    def _calculate_summary_stats(self, df: pd.DataFrame, chart_spec: ChartSpec) -> Dict[str, Any]:
        """Simple summary statistics."""
        stats = {
            "total_records": len(df),
            "chart_type": chart_spec.chart_type
        }
        
        # Add basic stats for numeric columns
        if chart_spec.y and chart_spec.y in df.columns:
            try:
                y_series = pd.to_numeric(df[chart_spec.y], errors='coerce').dropna()
                if len(y_series) > 0:
                    stats.update({
                        f"{chart_spec.y}_total": float(y_series.sum()),
                        f"{chart_spec.y}_mean": float(y_series.mean()),
                        f"{chart_spec.y}_min": float(y_series.min()),
                        f"{chart_spec.y}_max": float(y_series.max())
                    })
            except Exception:
                pass
        
        # Add categorical stats
        if chart_spec.x and chart_spec.x in df.columns:
            try:
                unique_count = df[chart_spec.x].nunique()
                stats[f"{chart_spec.x}_unique_count"] = unique_count
                stats[f"{chart_spec.x}_groups"] = unique_count
            except Exception:
                pass
        
        return stats