/**
 * API response and request types.
 * Similar to DTOs in .NET applications for type safety across boundaries.
 */

// Base API response wrapper
export interface ApiResponse<T = any> {
  data?: T;
  error?: ApiError;
  success: boolean;
}

export interface ApiError {
  message: string;
  type: string;
  details?: Record<string, any>;
}

// CSV Upload types
export interface CSVPreviewResponse {
  filename: string;
  file_id: string;
  rows_total: number;
  columns_total: number;
  preview_rows: Record<string, any>[];
  column_info: Record<string, string>;
  file_size_mb: number;
}

export interface CSVMetadata {
  filename: string;
  file_id: string;
  columns: string[];
  column_types: Record<string, string>;
  row_count: number;
  file_size_bytes: number;
  upload_timestamp: string;
}

// Chat types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  file_id: string;
  question: string;
  context?: ChatMessage[];
}

export interface ChatResponse {
  message: ChatMessage;
  chart_data?: ChartData;
  requires_clarification: boolean;
  clarification_prompt?: string;
  suggested_questions: string[];
}

// Chart types
export interface ChartSpec {
  chart_type: 'bar' | 'line' | 'scatter' | 'pie';
  x?: string;
  y?: string;
  aggregation?: 'sum' | 'mean' | 'count' | 'min' | 'max' | 'none';
  group_by?: string[];
  filters?: FilterSpec[];
  explanation: string;
  title?: string;
}

export interface FilterSpec {
  column: string;
  operator: '==' | '!=' | '>' | '>=' | '<' | '<=' | 'in' | 'not_in';
  value: string | number | (string | number)[];
}

export interface ChartData {
  chart_spec: ChartSpec;
  data: Record<string, any>[];
  summary_stats: Record<string, any>;
  data_transformations: string[];
}