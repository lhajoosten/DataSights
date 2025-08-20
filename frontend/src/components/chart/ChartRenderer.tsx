/**
 * Enhanced chart renderer with proper TypeScript types.
 * Follows Angular patterns with strong typing and null safety.
 */

import React from 'react';
import {
  BarChart,
  LineChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { clsx } from 'clsx';
import { ChartData } from '@/types/api';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';

interface ChartRendererProps {
  chartData: ChartData;
  className?: string;
}

interface ProcessedChartData {
  data: Record<string, any>[];
  seriesKeys: string[];
  colors: string[];
}

export const ChartRenderer: React.FC<ChartRendererProps> = ({
  chartData,
  className,
}) => {
  const { chart_spec, data, summary_stats } = chartData;

  // Color palette for multi-series charts
  const colorPalette = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', 
    '#8b5cf6', '#f97316', '#06b6d4', '#84cc16'
  ];

  /**
   * Process data for multi-dimensional visualization.
   * Handles grouping and reshaping for complex charts.
   * Follows TypeScript best practices with proper typing.
   */
  const processChartData = (): ProcessedChartData => {
    if (!data || data.length === 0) {
      return { data: [], seriesKeys: [], colors: [] };
    }

    // For simple charts (no group_by)
    if (!chart_spec.group_by || chart_spec.group_by.length === 0) {
      return {
        data,
        seriesKeys: [chart_spec.y || 'value'],
        colors: [colorPalette[0]]
      };
    }

    // For multi-dimensional charts
    const groupByKey = chart_spec.group_by[0]; // Primary grouping dimension
    const xKey = chart_spec.x;
    const yKey = chart_spec.y;

    if (!xKey || !yKey || !groupByKey) {
      return { data, seriesKeys: [yKey || 'value'], colors: [colorPalette[0]] };
    }

    // Reshape data for multi-series visualization
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
   * Reshape data for multi-series charts (grouped bars, multiple lines).
   * Follows functional programming patterns with proper type safety.
   */
  const reshapeForMultiSeries = (
    rawData: Record<string, any>[], 
    xKey: string, 
    yKey: string, 
    groupKey: string
  ): Record<string, any>[] => {
    const grouped = new Map<string, Record<string, any>>();

    rawData.forEach(item => {
      const xValue = String(item[xKey] ?? '');
      const yValue = Number(item[yKey]) || 0;
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