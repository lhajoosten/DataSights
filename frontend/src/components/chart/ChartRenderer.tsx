/**
 * Simplified chart renderer focused on reliability.
 * This component is responsible for rendering various types of charts
 * using the Recharts library, with a focus on handling data gracefully.
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

export const ChartRenderer: React.FC<ChartRendererProps> = ({
  chartData,
  className,
}) => {
  const { chart_spec, data, summary_stats } = chartData;

  // Debug logging
  console.log('Chart data received:', {
    chartType: chart_spec.chart_type,
    dataLength: data.length,
    data: data.slice(0, 3), // First 3 items for debugging
    xAxis: chart_spec.x,
    yAxis: chart_spec.y
  });

  // If no data, show message
  if (!data || data.length === 0) {
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

  const renderChart = () => {
    switch (chart_spec.chart_type) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey={chart_spec.x as any} 
                tick={{ fontSize: 12 }}
                angle={data.length > 10 ? -45 : 0}
                textAnchor={data.length > 10 ? 'end' : 'middle'}
                height={data.length > 10 ? 60 : 30}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar
                dataKey={chart_spec.y as any}
                fill="#3b82f6"
                name={chart_spec.y}
              />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey={chart_spec.x} 
                tick={{ fontSize: 12 }}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey={chart_spec.y as any}
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ r: 4 }}
                name={chart_spec.y}
              />
            </LineChart>
          </ResponsiveContainer>
        );

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

          {/* Debug Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm bg-gray-50 p-4 rounded">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Chart Details</h4>
              <div className="space-y-1 text-gray-600">
                <p><span className="font-medium">Type:</span> {chart_spec.chart_type}</p>
                <p><span className="font-medium">X-axis:</span> {chart_spec.x}</p>
                <p><span className="font-medium">Y-axis:</span> {chart_spec.y}</p>
                <p><span className="font-medium">Aggregation:</span> {chart_spec.aggregation}</p>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Summary Statistics</h4>
              <div className="space-y-1 text-gray-600">
                <p><span className="font-medium">Data points:</span> {summary_stats.total_records || 0}</p>
                {Object.entries(summary_stats)
                  .filter(([key]) => key !== 'total_records' && key !== 'chart_type')
                  .slice(0, 3)
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