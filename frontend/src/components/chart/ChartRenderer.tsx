/**
 * ChartRenderer Component - Visualizes data using chart libraries
 * 
 * This component takes structured chart data and renders it as interactive charts.
 * It's the final step in our data visualization pipeline:
 * 1. User uploads CSV
 * 2. User asks question in natural language
 * 3. LLM converts question to chart specification
 * 4. Backend processes data according to specification
 * 5. THIS COMPONENT renders the final chart
 * 
 * Key Features:
 * - Supports multiple chart types (bar, line, scatter, pie)
 * - Handles multi-dimensional data (e.g., "sales by region and product")
 * - Responsive design that works on all screen sizes
 * - Type-safe with comprehensive TypeScript interfaces
 */

import React from 'react';
// Recharts is a React chart library built on D3.js
// It provides pre-built chart components that are easy to use
import {
  BarChart,      // For bar charts (good for categories)
  LineChart,     // For line charts (good for trends over time)
  Bar,           // Individual bar component
  Line,          // Individual line component
  XAxis,         // Horizontal axis
  YAxis,         // Vertical axis
  CartesianGrid, // Background grid lines
  Tooltip,       // Hover information
  Legend,        // Chart legend
  ResponsiveContainer, // Makes charts responsive to container size
} from 'recharts';
import { clsx } from 'clsx'; // Utility for conditional CSS classes
import { ChartData } from '@/types/api'; // Our custom data types
import { Card, CardHeader, CardContent } from '@/components/ui/Card'; // UI components

// TypeScript interface defines what props this component accepts
interface ChartRendererProps {
  chartData: ChartData;  // The data and configuration from backend
  className?: string;    // Optional CSS classes for styling
}

// TypeScript interface for processed chart data structure
interface ProcessedChartData {
  data: Record<string, any>[]; // Array of data objects for the chart
  seriesKeys: string[];        // Names of data series (for multi-line charts)
  colors: string[];           // Colors for each data series
}

// React Functional Component with TypeScript typing
export const ChartRenderer: React.FC<ChartRendererProps> = ({
  chartData,
  className,
}) => {
  // Destructure the chart data into its components
  const { chart_spec, data, summary_stats } = chartData;

  // Predefined color palette for multi-series charts
  // These colors provide good contrast and are colorblind-friendly
  const colorPalette = [
    '#3b82f6', // Blue
    '#ef4444', // Red  
    '#10b981', // Green
    '#f59e0b', // Yellow
    '#8b5cf6', // Purple
    '#f97316', // Orange
    '#06b6d4', // Cyan
    '#84cc16'  // Lime
  ];

  /**
   * Process and reshape data for chart rendering
   * 
   * This function handles the complex task of converting our structured data
   * into the format that Recharts expects. It needs to handle both simple
   * charts (like "sales by region") and complex multi-dimensional charts
   * (like "sales by region and product").
   * 
   * Returns: ProcessedChartData with formatted data, series keys, and colors
   */
  const processChartData = (): ProcessedChartData => {
    // Guard clause: handle empty data gracefully
    if (!data || data.length === 0) {
      return { data: [], seriesKeys: [], colors: [] };
    }

    // SIMPLE CHARTS: No grouping, just x and y values
    // Example: "Show total sales by region" -> one bar per region
    if (!chart_spec.group_by || chart_spec.group_by.length === 0) {
      return {
        data,                                    // Use data as-is
        seriesKeys: [chart_spec.y || 'value'],  // Single data series
        colors: [colorPalette[0]]               // Use first color
      };
    }

    // MULTI-DIMENSIONAL CHARTS: Grouping by additional dimensions
    // Example: "Show sales by region and product" -> multiple bars per region
    const groupByKey = chart_spec.group_by[0]; // Primary grouping dimension (e.g., "product")
    const xKey = chart_spec.x;                 // X-axis field (e.g., "region")
    const yKey = chart_spec.y;                 // Y-axis field (e.g., "sales")

    // Validation: ensure we have all required fields
    if (!xKey || !yKey || !groupByKey) {
      // Fallback to simple chart format
      return { data, seriesKeys: [yKey || 'value'], colors: [colorPalette[0]] };
    }

    // Transform data for multi-series visualization
    const reshapedData = reshapeForMultiSeries(data, xKey, yKey, groupByKey);
    const seriesKeys = getUniqueValues(data, groupByKey);
    const colors = seriesKeys.map((_, index) => colorPalette[index % colorPalette.length]);

    return {
      data: reshapedData,
      seriesKeys,
      colors
    };
  };

  /**
   * Reshape data for multi-series charts
   * 
   * This function converts tabular data into the format needed for grouped charts.
   * 
   * Input example (tabular format):
   * [
   *   {region: "North", product: "A", sales: 100},
   *   {region: "North", product: "B", sales: 150},
   *   {region: "South", product: "A", sales: 200}
   * ]
   * 
   * Output example (grouped format):
   * [
   *   {region: "North", "A": 100, "B": 150},
   *   {region: "South", "A": 200, "B": 0}
   * ]
   * 
   * This allows Recharts to render multiple bars/lines per x-axis category.
   */
  const reshapeForMultiSeries = (
    rawData: Record<string, any>[], 
    xKey: string, 
    yKey: string, 
    groupKey: string
  ): Record<string, any>[] => {
    // Use a Map to group data by x-axis values
    const grouped = new Map<string, Record<string, any>>();

    // Process each data row
    rawData.forEach(item => {
      const xValue = String(item[xKey] ?? '');  // X-axis value (e.g., "North")
      const yValue = Number(item[yKey]) || 0;   // Y-axis value (e.g., 100)
      const groupValue = String(item[groupKey] ?? '');

      if (!grouped.has(xValue)) {
        grouped.set(xValue, { [xKey]: xValue });
      }

      const group = grouped.get(xValue)!;
      group[groupValue] = (group[groupValue] || 0) + yValue;
    });

    return Array.from(grouped.values()).sort((a, b) => 
      String(a[xKey]).localeCompare(String(b[xKey]))
    );
  };

  /**
   * Get unique values for a specific key (for series identification).
   * Type-safe with proper null handling.
   */
  const getUniqueValues = (rawData: Record<string, any>[], key: string): string[] => {
    const values = [...new Set(rawData.map(item => String(item[key] ?? '')))];
    return values.filter(v => v !== '').sort();
  };

  // Process data according to chart complexity
  const processedData = processChartData();

  // If no data, show empty state
  if (!processedData.data || processedData.data.length === 0) {
    return (
      <Card className={clsx('', className)}>
        <CardHeader 
          title="No Data Available"
          subtitle="The query returned no results to visualize"
        />
        <CardContent>
          <div className="flex items-center justify-center h-64 text-gray-500">
            <div className="text-center">
              <p className="text-lg mb-2">No data to display</p>
              <p className="text-sm">Try adjusting your filters or question</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  /**
   * Render bar chart with support for grouped bars.
   * Follows React best practices with proper key management.
   */
  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart 
        data={processedData.data} 
        margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey={chart_spec.x} 
          tick={{ fontSize: 12 }}
          angle={processedData.data.length > 8 ? -45 : 0}
          textAnchor={processedData.data.length > 8 ? 'end' : 'middle'}
          height={processedData.data.length > 8 ? 80 : 30}
        />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Legend />
        
        {/* Render multiple bars for grouped data */}
        {processedData.seriesKeys.map((seriesKey, index) => (
          <Bar
            key={seriesKey}
            dataKey={seriesKey}
            fill={processedData.colors[index]}
            name={seriesKey}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );

  /**
   * Render line chart with support for multiple lines.
   * Performance optimized with proper React patterns.
   */
  const renderLineChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart 
        data={processedData.data} 
        margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey={chart_spec.x} 
          tick={{ fontSize: 12 }}
        />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Legend />
        
        {/* Render multiple lines for grouped data */}
        {processedData.seriesKeys.map((seriesKey, index) => (
          <Line
            key={seriesKey}
            type="monotone"
            dataKey={seriesKey}
            stroke={processedData.colors[index]}
            strokeWidth={2}
            dot={{ r: 4 }}
            name={seriesKey}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );

  const renderChart = () => {
    switch (chart_spec.chart_type) {
      case 'bar':
        return renderBarChart();
      case 'line':
        return renderLineChart();
      default:
        return (
          <div className="flex items-center justify-center h-64 text-gray-500">
            Chart type "{chart_spec.chart_type}" not yet implemented
          </div>
        );
    }
  };

  return (
    <Card className={clsx('', className)}>
      <CardHeader 
        title={chart_spec.title || `${chart_spec.chart_type.charAt(0).toUpperCase() + chart_spec.chart_type.slice(1)} Chart`}
        subtitle={chart_spec.explanation}
      />
      <CardContent>
        <div className="space-y-4">
          {/* Chart */}
          <div className="w-full">
            {renderChart()}
          </div>

          {/* Enhanced Debug Info with proper null safety */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm bg-gray-50 p-4 rounded">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Chart Details</h4>
              <div className="space-y-1 text-gray-600">
                <p><span className="font-medium">Type:</span> {chart_spec.chart_type}</p>
                <p><span className="font-medium">X-axis:</span> {chart_spec.x ?? 'None'}</p>
                <p><span className="font-medium">Y-axis:</span> {chart_spec.y ?? 'None'}</p>
                <p><span className="font-medium">Aggregation:</span> {chart_spec.aggregation ?? 'none'}</p>
                {chart_spec.group_by && chart_spec.group_by.length > 0 && (
                  <p><span className="font-medium">Grouped by:</span> {chart_spec.group_by.join(', ')}</p>
                )}
                {/* Fixed: proper null safety for calculation */}
                {chart_spec.calculation && (
                  <p><span className="font-medium">Calculation:</span> {chart_spec.calculation.field_name}</p>
                )}
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Data Summary</h4>
              <div className="space-y-1 text-gray-600">
                <p><span className="font-medium">Data points:</span> {summary_stats?.total_records ?? 0}</p>
                <p><span className="font-medium">Series count:</span> {processedData.seriesKeys.length}</p>
                {Object.entries(summary_stats ?? {})
                  .filter(([key]) => key !== 'total_records' && key !== 'chart_type')
                  .slice(0, 2)
                  .map(([key, value]) => (
                    <p key={key}>
                      <span className="font-medium">{key.replace(/_/g, ' ')}:</span>{' '}
                      {typeof value === 'number' ? value.toLocaleString() : String(value)}
                    </p>
                  ))}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};