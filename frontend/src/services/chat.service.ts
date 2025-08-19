/**
 * Chat and chart generation service.
 * Similar to conversation services in .NET applications.
 */

import { ApiService } from './api.service';
import { ChatRequest, ChatResponse, ChartData, ApiResponse } from '@/types/api';

export class ChatService {
  /**
   * Send question about CSV data
   */
  static async askQuestion(request: ChatRequest): Promise<ApiResponse<ChatResponse>> {
    return ApiService.post<ChatResponse>('/chat/ask', request);
  }

  /**
   * Validate chart specification
   */
  static async validateChart(
    chartSpec: any, 
    fileId: string
  ): Promise<ApiResponse<any>> {
    return ApiService.post<any>('/chat/validate-chart', {
      data: chartSpec,
      params: { file_id: fileId }
    });
  }

  /**
   * Generate suggested questions based on CSV data
   * Client-side heuristics similar to business logic in .NET
   */
  static generateSuggestedQuestions(
    columnInfo: Record<string, string>
  ): string[] {
    const suggestions: string[] = [];
    const columns = Object.keys(columnInfo);
    const numericColumns = columns.filter(col => 
      ['integer', 'float', 'number'].includes(columnInfo[col])
    );
    const categoricalColumns = columns.filter(col => 
      ['string', 'category'].includes(columnInfo[col])
    );
    const dateColumns = columns.filter(col => 
      ['datetime', 'date'].includes(columnInfo[col])
    );

    // Time-based suggestions
    if (dateColumns.length > 0 && numericColumns.length > 0) {
      suggestions.push(`Show ${numericColumns[0]} trends over time`);
      suggestions.push(`Compare ${numericColumns[0]} by month`);
    }

    // Categorical breakdown suggestions
    if (categoricalColumns.length > 0 && numericColumns.length > 0) {
      suggestions.push(`Show ${numericColumns[0]} by ${categoricalColumns[0]}`);
      suggestions.push(`Compare total ${numericColumns[0]} across ${categoricalColumns[0]}`);
    }

    // Correlation suggestions
    if (numericColumns.length >= 2) {
      suggestions.push(`Show relationship between ${numericColumns[0]} and ${numericColumns[1]}`);
    }

    // Summary suggestions
    if (numericColumns.length > 0) {
      suggestions.push(`Show summary statistics for ${numericColumns[0]}`);
      suggestions.push(`What are the top values in ${numericColumns[0]}?`);
    }

    // Fallback suggestions
    if (suggestions.length === 0) {
      suggestions.push('Show me a summary of this data');
      suggestions.push('Create a chart from this data');
      suggestions.push('What patterns can you find?');
    }

    return suggestions.slice(0, 6); // Limit to 6 suggestions
  }

  /**
   * Format chart data for different visualization libraries
   * Similar to data transformation services in .NET
   */
  static formatChartDataForRecharts(chartData: ChartData): any {
    const { chart_spec, data } = chartData;

    // Base configuration for Recharts
    const config = {
      data: data,
      chartType: chart_spec.chart_type,
      xKey: chart_spec.x,
      yKey: chart_spec.y,
      title: chart_spec.title || chart_spec.explanation
    };

    // Chart-specific formatting
    switch (chart_spec.chart_type) {
      case 'pie':
        return {
          ...config,
          data: data.map(item => ({
            name: item.name || item[chart_spec.x || ''],
            value: item.value || item[chart_spec.y || '']
          }))
        };

      case 'bar':
      case 'line':
        return {
          ...config,
          data: data.map(item => {
            const formattedItem: any = {};
            Object.keys(item).forEach(key => {
              formattedItem[key] = item[key];
            });
            return formattedItem;
          })
        };

      case 'scatter':
        return {
          ...config,
          data: data.map(item => ({
            x: item[chart_spec.x || ''],
            y: item[chart_spec.y || ''],
            ...item
          }))
        };

      default:
        return config;
    }
  }
}