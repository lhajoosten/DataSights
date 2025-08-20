/**
 * Generic chat service that works with any data structure.
 */

import { ApiService } from "./api.service";
import { ChatRequest, ChatResponse, ChartData, ApiResponse } from "@/types/api";

export class ChatService {
  /**
   * Send question about CSV data
   */
  static async askQuestion(
    request: ChatRequest
  ): Promise<ApiResponse<ChatResponse>> {
    return ApiService.post<ChatResponse>("/chat/ask", request);
  }

  /**
   * Validate chart specification
   */
  static async validateChart(
    chartSpec: any,
    fileId: string
  ): Promise<ApiResponse<any>> {
    return ApiService.post<any>(
      `/chat/validate-chart?file_id=${fileId}`,
      chartSpec
    );
  }

  /**
   * Generate completely generic suggested questions based on data structure.
   * Works with any CSV regardless of column names or domain.
   */
  static generateSuggestedQuestions(
    columnInfo: Record<string, string>
  ): string[] {
    const suggestions: string[] = [];
    const columns = Object.keys(columnInfo);

    // Categorize columns by type
    const numericColumns = columns.filter((col) =>
      ["integer", "float", "number"].includes(columnInfo[col])
    );
    const categoricalColumns = columns.filter((col) =>
      ["string", "category"].includes(columnInfo[col])
    );
    const dateColumns = columns.filter((col) =>
      ["datetime", "date"].includes(columnInfo[col])
    );

    // Generic time-based suggestions
    if (dateColumns.length > 0 && numericColumns.length > 0) {
      suggestions.push(`Show ${numericColumns[0]} trends over time`);
      suggestions.push(`Show ${numericColumns[0]} by month`);
      if (categoricalColumns.length > 0) {
        suggestions.push(
          `Compare ${numericColumns[0]} by ${categoricalColumns[0]} over time`
        );
      }
    }

    // Generic categorical breakdown suggestions
    if (categoricalColumns.length > 0 && numericColumns.length > 0) {
      suggestions.push(`Show ${numericColumns[0]} by ${categoricalColumns[0]}`);
      suggestions.push(
        `Compare total ${numericColumns[0]} across ${categoricalColumns[0]}`
      );

      // Multi-dimensional suggestions
      if (categoricalColumns.length > 1) {
        suggestions.push(
          `Show ${numericColumns[0]} by ${categoricalColumns[0]} and ${categoricalColumns[1]}`
        );
      }
    }

    // Generic relationship suggestions
    if (numericColumns.length >= 2) {
      suggestions.push(
        `Show relationship between ${numericColumns[0]} and ${numericColumns[1]}`
      );
      suggestions.push(
        `Create scatter plot of ${numericColumns[0]} vs ${numericColumns[1]}`
      );
    }

    // Generic calculation suggestions
    if (numericColumns.length >= 2) {
      suggestions.push(
        `Calculate ${numericColumns[0]} times ${numericColumns[1]}`
      );
      suggestions.push(
        `Show ratio of ${numericColumns[0]} to ${numericColumns[1]}`
      );
    }

    // Generic summary suggestions
    if (numericColumns.length > 0) {
      suggestions.push(`Show summary statistics for ${numericColumns[0]}`);
      suggestions.push(`What are the top values in ${numericColumns[0]}?`);
    }

    // Generic distribution suggestions
    if (categoricalColumns.length > 0 && numericColumns.length > 0) {
      suggestions.push(
        `Show distribution of ${numericColumns[0]} by ${categoricalColumns[0]}`
      );
    }

    // Fallback suggestions for any data
    if (suggestions.length === 0) {
      suggestions.push("Show me a summary of this data");
      suggestions.push("Create a bar chart from this data");
      suggestions.push("What patterns can you find?");
      suggestions.push("Compare the different categories");
    }

    // Return up to 6 most relevant suggestions
    return suggestions.slice(0, 6);
  }

  /**
   * Format chart data for different visualization libraries
   * Works with any data structure
   */
  static formatChartDataForRecharts(chartData: ChartData): any {
    const { chart_spec, data } = chartData;

    // Base configuration for Recharts
    const config = {
      data: data,
      chartType: chart_spec.chart_type,
      xKey: chart_spec.x,
      yKey: chart_spec.y,
      title: chart_spec.title || chart_spec.explanation,
    };

    // Chart-specific formatting (same as before but more generic)
    switch (chart_spec.chart_type) {
      case "pie":
        return {
          ...config,
          data: data.map((item) => ({
            name: item.name || item[chart_spec.x || ""] || "Unknown",
            value: item.value || item[chart_spec.y || ""] || 0,
          })),
        };

      case "bar":
      case "line":
        return {
          ...config,
          data: data.map((item) => {
            const formattedItem: any = {};
            Object.keys(item).forEach((key) => {
              formattedItem[key] = item[key];
            });
            return formattedItem;
          }),
        };

      case "scatter":
        return {
          ...config,
          data: data.map((item) => ({
            x: item[chart_spec.x || ""] || 0,
            y: item[chart_spec.y || ""] || 0,
            ...item,
          })),
        };

      default:
        return config;
    }
  }
}
