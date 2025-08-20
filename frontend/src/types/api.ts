/**
 * API types matching the enhanced backend models.
 * Following Angular/TypeScript conventions with proper typing.
 */

// Enhanced chart specification types
export interface CalculationSpec {
  field_name: string;
  formula: string;
  description: string;
}

export interface FilterSpec {
  column: string;
  operator: '==' | '!=' | '>' | '>=' | '<' | '<=' | 'in' | 'not_in';
  value: string | number | (string | number)[];
}

export interface ChartSpec {
  chart_type: 'bar' | 'line' | 'scatter' | 'pie';
  x?: string;
  y?: string;
  aggregation?: 'sum' | 'mean' | 'count' | 'min' | 'max' | 'none';
  group_by?: string[];
  calculation?: CalculationSpec;  // Added this field
  filters?: FilterSpec[];
  explanation?: string;  // Made optional to match backend
  title?: string;
}

export interface ChartData {
  chart_spec: ChartSpec;
  data: Record<string, any>[];
  summary_stats: Record<string, any>;
  data_transformations: string[];
}

// Chat and response types
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

// CSV related types
export interface CSVPreviewResponse {
  filename: string;
  rows_total: number;
  columns_total: number;
  preview_rows: Record<string, any>[];
  column_info: Record<string, string>;
  file_size_mb: number;
  file_id: string;
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

// API response wrapper
export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  success: boolean;
}

export interface ApiError {
  message: string;
  type: string;
  details: Record<string, any>;
}