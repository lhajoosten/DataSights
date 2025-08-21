"""
Chart Service - Transforms raw CSV data into chart-ready format

This service takes structured chart specifications (from the LLM service)
and applies them to raw CSV data to create properly formatted chart data.

Key Responsibilities:
1. Data transformations (filtering, grouping, aggregating)
2. Calculated fields (like revenue = units_sold * unit_price)
3. Data validation and error handling
4. Format conversion for frontend chart libraries

Think of this as the "data processor" that takes instructions and raw data,
then outputs perfectly formatted data ready for visualization.
"""

import pandas as pd  # Data manipulation library
import numpy as np   # Numerical operations
from typing import Dict, List, Any, Optional, Tuple
import logging

# Import our custom data models
from app.models.chart_models import ChartSpec, ChartData, ChartValidationResult, FilterSpec
from app.models.csv_models import CSVMetadata
from app.core.exceptions import ValidationException, FileProcessingException

# Set up logging for debugging
logger = logging.getLogger(__name__)


class ChartService:
    """
    Chart Service - The "data processor" that prepares data for visualization
    
    This class handles all the data manipulation needed to create charts:
    - Taking raw CSV data and chart specifications
    - Applying filters, grouping, and aggregations
    - Calculating derived fields (like revenue from units * price)
    - Formatting the final data for frontend chart libraries
    
    The service follows a pipeline pattern: data flows through multiple
    transformation steps, each one preparing it for the next step.
    """
    
    def __init__(self):
        """
        Initialize the chart service with default limits
        
        These limits prevent performance issues with very large datasets:
        - max_data_points: Prevents charts from becoming unreadable
        - max_categories: Prevents too many bars/lines in a single chart
        """
        self.max_data_points = 1000  # Maximum points to display on a chart
        self.max_categories = 50     # Maximum categories (bars, lines, etc.)
    
    async def generate_chart_data(
        self, 
        chart_spec: ChartSpec, 
        dataframe: pd.DataFrame,
        csv_metadata: CSVMetadata
    ) -> ChartData:
        """
        MAIN METHOD: Transform raw data into chart-ready format
        
        This is the primary method that orchestrates the entire data transformation
        pipeline. It takes a chart specification (what the user wants) and raw CSV
        data, then applies a series of transformations to create the final chart data.
        
        Parameters:
        - chart_spec: Instructions for what chart to create (from LLM service)
        - dataframe: Raw CSV data as a pandas DataFrame
        - csv_metadata: Information about the CSV structure
        
        Returns:
        - ChartData: Formatted data ready for frontend chart rendering
        
        The transformation pipeline:
        1. Handle time-based operations (extract month from dates)
        2. Calculate derived fields (revenue = units * price)
        3. Apply any filters (only show data from 2024)
        4. Apply grouping and aggregation (sum sales by region)
        5. Format for frontend consumption
        6. Add summary statistics
        """
        try:
            # Log what we're about to process for debugging
            logger.info(f"Starting chart generation: {chart_spec.chart_type}")
            logger.info(f"Chart spec: X={chart_spec.x}, Y={chart_spec.y}, GroupBy={chart_spec.group_by}")
            logger.info(f"Input data shape: {dataframe.shape} (rows x columns)")
            
            # PIPELINE PATTERN: Each step transforms the data for the next step
            # Start with a copy to avoid modifying the original data
            df = dataframe.copy()
            
            # Track what transformations we apply (for debugging and user feedback)
            transformations = []
            
            # STEP 1: Handle time-based grouping (extract month from date columns)
            # If user asks for "sales by month", we need to extract month from date column
            if chart_spec.x and 'month' in chart_spec.x.lower():
                df, time_transformations = self._extract_month_from_date(df)
                transformations.extend(time_transformations)
                logger.info(f"After time extraction: {df.shape}")
            
            # STEP 2: Calculate derived fields (like revenue = units_sold * unit_price)
            # Many business questions involve calculated metrics not directly in the data
            if chart_spec.y == 'revenue' and 'revenue' not in df.columns:
                df, calc_transformations = self._calculate_revenue_if_possible(df)
                transformations.extend(calc_transformations)
                logger.info(f"After revenue calculation: {df.shape}")
            
            # STEP 3: Apply any filters (like "only show data from 2024")
            if chart_spec.filters:
                df, filter_transformations = self._apply_filters(df, chart_spec.filters)
                transformations.extend(filter_transformations)
                logger.info(f"After filters: {df.shape}")
            
            # STEP 4: Apply grouping and aggregation (the core of most charts)
            # This is where "sum sales by region" becomes actual grouped data
            if chart_spec.aggregation != "none" or chart_spec.group_by:
                df, agg_transformations = self._apply_aggregation(df, chart_spec)
                transformations.extend(agg_transformations)
                logger.info(f"After aggregation: {df.shape}")
            
            # STEP 5: Validate we still have data to work with
            if df.empty:
                logger.warning("No data remaining after processing")
                return self._create_empty_result(chart_spec, transformations)
            
            # STEP 6: Format data for frontend chart libraries (Recharts)
            chart_data = self._format_for_frontend(chart_spec, df)
            logger.info(f"Generated {len(chart_data)} data points for chart")
            
            # STEP 7: Calculate summary statistics for user insights
            summary_stats = self._calculate_summary_stats(df, chart_spec)
            
            return ChartData(
                chart_spec=chart_spec,
                data=chart_data,
                summary_stats=summary_stats,
                data_transformations=transformations
            )
            
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}", exc_info=True)
            raise FileProcessingException(f"Chart generation failed: {str(e)}")
    
    def _calculate_revenue_if_possible(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Simple revenue calculation if units_sold and unit_price exist.
        Follows .NET defensive programming patterns.
        """
        transformations = []
        
        if 'units_sold' in df.columns and 'unit_price' in df.columns:
            try:
                # Convert to numeric
                df['units_sold'] = pd.to_numeric(df['units_sold'], errors='coerce')
                df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
                
                # Calculate revenue
                df['revenue'] = df['units_sold'] * df['unit_price']
                df['revenue'] = df['revenue'].fillna(0)
                
                transformations.append("Calculated revenue = units_sold * unit_price")
                logger.info(f"Revenue calculation successful. Sample: {df['revenue'].head(3).tolist()}")
                
            except Exception as e:
                logger.error(f"Revenue calculation failed: {str(e)}")
                transformations.append(f"Revenue calculation failed: {str(e)}")
        else:
            logger.warning("Cannot calculate revenue - missing units_sold or unit_price columns")
        
        return df, transformations
    
    def _extract_month_from_date(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Extract month from date column - robust date handling."""
        transformations = []
        
        date_col = self._find_date_column(df)
        if date_col:
            try:
                df['month'] = pd.to_datetime(df[date_col]).dt.to_period('M').astype(str)
                transformations.append(f"Extracted month from {date_col}")
                logger.info(f"Month extraction successful from {date_col}")
            except Exception as e:
                logger.warning(f"Month extraction failed: {str(e)}")
        
        return df, transformations
    
    def _apply_aggregation(
        self, 
        df: pd.DataFrame, 
        chart_spec: ChartSpec
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Apply aggregation with multi-dimensional grouping support.
        Follows Repository pattern - encapsulates data access logic.
        """
        transformations = []
        
        if chart_spec.aggregation == "none" and not chart_spec.group_by:
            return df, transformations
        
        # Determine grouping strategy
        group_cols = self._determine_grouping_columns(chart_spec, df)
        
        if not group_cols:
            logger.warning("No valid grouping columns")
            return df, transformations
        
        try:
            logger.info(f"Grouping by: {group_cols}")
            
            if chart_spec.aggregation == "count":
                agg_df = df.groupby(group_cols).size().reset_index(name='count')
                if not chart_spec.y:
                    chart_spec.y = 'count'
                transformations.append(f"Grouped by {group_cols} and counted rows")
                
            elif chart_spec.y and chart_spec.y in df.columns:
                agg_func = self._get_aggregation_function(chart_spec.aggregation)
                
                # Convert target column to numeric
                df[chart_spec.y] = pd.to_numeric(df[chart_spec.y], errors='coerce')
                
                # Perform aggregation
                agg_df = df.groupby(group_cols)[chart_spec.y].agg(agg_func).reset_index()
                transformations.append(f"Grouped by {group_cols}, applied {agg_func} to {chart_spec.y}")
            else:
                logger.warning(f"Y column '{chart_spec.y}' not found")
                return df, transformations
            
            logger.info(f"Aggregation result: {agg_df.shape}")
            if not agg_df.empty:
                logger.info(f"Sample data: {agg_df.head(2).to_dict('records')}")
            
            return agg_df, transformations
            
        except Exception as e:
            logger.error(f"Aggregation failed: {str(e)}")
            return df, transformations
    
    def _determine_grouping_columns(self, chart_spec: ChartSpec, df: pd.DataFrame) -> List[str]:
        """
        Determine grouping columns based on chart specification.
        Follows Strategy pattern - encapsulates grouping logic.
        """
        group_cols = []
        
        # Add explicit group_by columns
        if chart_spec.group_by:
            group_cols.extend(chart_spec.group_by)
        
        # Add X-axis as grouping dimension if not already included
        if chart_spec.x and chart_spec.x not in group_cols and chart_spec.x in df.columns:
            group_cols.append(chart_spec.x)
        
        # Filter out non-existent columns
        valid_cols = [col for col in group_cols if col in df.columns]
        return valid_cols
    
    def _get_aggregation_function(self, aggregation: str) -> str:
        """Get pandas aggregation function name - simple mapping."""
        function_map = {
            "sum": "sum",
            "mean": "mean",
            "min": "min",
            "max": "max"
        }
        return function_map.get(aggregation, "sum")
    
    def _format_for_frontend(self, chart_spec: ChartSpec, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Format data for frontend consumption.
        Follows DTO pattern - data transfer objects for API communication.
        """
        data = []
        
        logger.info(f"Formatting {len(df)} rows")
        logger.info(f"Available columns: {list(df.columns)}")
        
        for _, row in df.iterrows():
            point = {}
            
            # Add all columns to support multi-dimensional charts
            for col in df.columns:
                value = row[col]
                point[col] = self._format_value_for_json(value)
            
            data.append(point)
        
        logger.info(f"Formatted {len(data)} data points")
        if data:
            logger.info(f"Sample point: {data[0]}")
        
        return data
    
    def _format_value_for_json(self, value: Any) -> Any:
        """Format value for JSON serialization - defensive type handling."""
        if pd.isna(value):
            return None
        elif isinstance(value, (np.integer, np.int64)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64)):
            return float(value)
        elif isinstance(value, pd.Timestamp):
            return value.isoformat()
        elif hasattr(value, 'item'):  # numpy scalar
            return value.item()
        else:
            return str(value)
    
    def _find_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find date column using heuristics."""
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    sample = df[col].dropna().head(5)
                    pd.to_datetime(sample, errors='raise')
                    return col
                except:
                    continue
        return None
    
    def _apply_filters(self, df: pd.DataFrame, filters: List[FilterSpec]) -> Tuple[pd.DataFrame, List[str]]:
        """Apply filters with defensive error handling."""
        transformations = []
        
        for filter_spec in filters:
            col = filter_spec.column
            op = filter_spec.operator
            value = filter_spec.value
            
            if col not in df.columns:
                logger.warning(f"Filter column '{col}' not found")
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
                
                final_rows = len(df)
                transformations.append(f"Filtered {col} {op} {value} ({initial_rows} → {final_rows} rows)")
                
            except Exception as e:
                logger.warning(f"Filter failed: {str(e)}")
                continue
        
        return df, transformations
    
    def _calculate_summary_stats(self, df: pd.DataFrame, chart_spec: ChartSpec) -> Dict[str, Any]:
        """Calculate summary statistics - following .NET's structured approach."""
        stats = {
            "total_records": len(df),
            "chart_type": chart_spec.chart_type
        }
        
        # Add Y-axis statistics
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
        
        # Add grouping statistics
        if chart_spec.x and chart_spec.x in df.columns:
            try:
                unique_count = df[chart_spec.x].nunique()
                stats[f"{chart_spec.x}_unique_count"] = unique_count
            except Exception:
                pass
        
        return stats
    
    def _create_empty_result(self, chart_spec: ChartSpec, transformations: List[str]) -> ChartData:
        """Create empty result with error info - defensive programming."""
        return ChartData(
            chart_spec=chart_spec,
            data=[],
            summary_stats={"total_records": 0, "error": "No data after processing"},
            data_transformations=transformations
        )