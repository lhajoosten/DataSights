/**
 * Chart rendering component using Recharts.
 * Similar to chart components in Angular with d3.js or Chart.js.
 */

import React from 'react';
import {
  BarChart,
  LineChart,
  ScatterChart,
  PieChart,
  Bar,
  Line,
  Scatter,
  Pie,
  Cell,
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

// Color palette for charts
const CHART_COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1'
];

export const ChartRenderer: React.FC<ChartRendererProps> = ({
  chartData,
  className,
}) => {
  const { chart_spec, data, summary_stats } = chartData;

  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey={chart_spec.x} 
          tick={{ fontSize: 12 }}
          angle={data.length > 10 ? -45 : 0}
          textAnchor={data.length > 10 ? 'end' : 'middle'}
          height={data.length > 10 ? 60 : 30}
        />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip 
          formatter={(value, name) => [
            typeof value === 'number' ? value.toLocaleString() : value,
            name
          ]}
          labelFormatter={(label) => `${chart_spec.x}: ${label}`}
        />
        <Legend />
        {chart_spec.group_by && chart_spec.group_by.length > 0 ? (
          // Grouped bar chart
          chart_spec.group_by.map((groupKey, index) => (
            <Bar
              key={groupKey}
              dataKey={chart_spec.y as any} // cast to satisfy DataKey<any> when y may be optional
              fill={CHART_COLORS[index % CHART_COLORS.length]}
              name={chart_spec.y}
            />
          ))
        ) : (
          <Bar
            dataKey={chart_spec.y as any} // cast to satisfy DataKey<any>
            fill={CHART_COLORS[0]}
            name={chart_spec.y}
          />
        )}
      </BarChart>
    </ResponsiveContainer>
  );

  const renderLineChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey={chart_spec.x} 
          tick={{ fontSize: 12 }}
        />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip 
          formatter={(value, name) => [
            typeof value === 'number' ? value.toLocaleString() : value,
            name
          ]}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey={chart_spec.y as any} // cast to satisfy DataKey<any>
          stroke={CHART_COLORS[0]}
          strokeWidth={2}
          dot={{ r: 4 }}
          name={chart_spec.y}
        />
      </LineChart>
    </ResponsiveContainer>
  );

  const renderScatterChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <ScatterChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          type="number"
          dataKey={chart_spec.x} 
          tick={{ fontSize: 12 }}
          name={chart_spec.x}
        />
        <YAxis 
          type="number"
          dataKey={chart_spec.y} 
          tick={{ fontSize: 12 }}
          name={chart_spec.y}
        />
        <Tooltip 
          formatter={(value, name) => [
            typeof value === 'number' ? value.toLocaleString() : value,
            name
          ]}
          cursor={{ strokeDasharray: '3 3' }}
        />
        <Scatter
          name="Data Points"
          dataKey={chart_spec.y as any} // cast to satisfy DataKey<any>
          fill={CHART_COLORS[0]}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );

  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          outerRadius={120}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((_, index) => ( // use _ for unused first param
            <Cell 
              key={`cell-${index}`} 
              fill={CHART_COLORS[index % CHART_COLORS.length]} 
            />
          ))}
        </Pie>
        <Tooltip 
          formatter={(value) => [
            typeof value === 'number' ? value.toLocaleString() : value,
            'Value'
          ]}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );

  const renderChart = () => {
    switch (chart_spec.chart_type) {
      case 'bar':
        return renderBarChart();
      case 'line':
        return renderLineChart();
      case 'scatter':
        return renderScatterChart();
      case 'pie':
        return renderPieChart();
      default:
        return (
          <div className="flex items-center justify-center h-64 text-gray-500">
            Unsupported chart type: {chart_spec.chart_type}
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

          {/* Chart Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Chart Details</h4>
              <div className="space-y-1 text-gray-600">
                <p><span className="font-medium">Type:</span> {chart_spec.chart_type}</p>
                {chart_spec.x && <p><span className="font-medium">X-axis:</span> {chart_spec.x}</p>}
                {chart_spec.y && <p><span className="font-medium">Y-axis:</span> {chart_spec.y}</p>}
                {chart_spec.aggregation && chart_spec.aggregation !== 'none' && (
                  <p><span className="font-medium">Aggregation:</span> {chart_spec.aggregation}</p>
                )}
                {chart_spec.group_by && chart_spec.group_by.length > 0 && (
                  <p><span className="font-medium">Grouped by:</span> {chart_spec.group_by.join(', ')}</p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Summary Statistics</h4>
              <div className="space-y-1 text-gray-600">
                <p><span className="font-medium">Data points:</span> {summary_stats.total_records?.toLocaleString() || 'N/A'}</p>
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

          {/* Data Transformations */}
          {chartData.data_transformations.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Data Transformations Applied</h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                {chartData.data_transformations.map((transformation, index) => (
                  <li key={index}>{transformation}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};