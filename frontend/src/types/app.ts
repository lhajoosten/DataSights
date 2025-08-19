import { CSVPreviewResponse, ChatMessage, ApiError } from '@/types/api';

/**
 * Application-specific types and enums.
 * Similar to domain models in .NET applications.
 */

export enum UploadStatus {
  Idle = 'idle',
  Uploading = 'uploading',
  Processing = 'processing',
  Success = 'success',
  Error = 'error'
}

export enum ChatStatus {
  Idle = 'idle',
  Thinking = 'thinking',
  Success = 'success',
  Error = 'error',
  NeedsClarification = 'needs_clarification'
}

export interface AppState {
  currentFile?: CSVPreviewResponse;
  chatHistory: ChatMessage[];
  isLoading: boolean;
  error: string | ApiError;
}

export interface UploadState {
  status: UploadStatus;
  progress: number;
  error?: string;
  file?: File;
}

export interface ChatState {
  status: ChatStatus;
  currentQuestion: string;
  error?: string;
  clarificationPrompt?: string;
  suggestedQuestions: string[];
}

// UI Component Props interfaces
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface LoadingProps extends BaseComponentProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export interface ErrorProps extends BaseComponentProps {
  error: string | ApiError;
  onRetry?: () => void;
  showRetry?: boolean;
}