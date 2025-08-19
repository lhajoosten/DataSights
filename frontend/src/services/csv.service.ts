/**
 * CSV-specific API service.
 * Similar to domain-specific services in .NET applications.
 */

import { ApiService } from './api.service';
import { CSVPreviewResponse, CSVMetadata, ApiResponse } from '@/types/api';

export class CSVService {
  /**
   * Upload CSV file and get preview data
   */
  static async uploadCSV(
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<CSVPreviewResponse>> {
    return ApiService.uploadFile<CSVPreviewResponse>(
      '/csv/upload',
      file,
      onProgress
    );
  }

  /**
   * Get CSV metadata by file ID
   */
  static async getMetadata(fileId: string): Promise<ApiResponse<CSVMetadata>> {
    return ApiService.get<CSVMetadata>(`/csv/${fileId}/metadata`);
  }

  /**
   * Delete uploaded CSV file
   */
  static async deleteFile(fileId: string): Promise<ApiResponse<void>> {
    return ApiService.delete<void>(`/csv/${fileId}`);
  }

  /**
   * Validate file before upload
   * Client-side validation similar to FluentValidation patterns
   */
  static validateFile(file: File): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    const maxSize = 10 * 1024 * 1024; // 10MB

    // Check file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
      errors.push('Only CSV files are allowed');
    }

    // Check file size
    if (file.size > maxSize) {
      errors.push(`File size ${(file.size / (1024 * 1024)).toFixed(2)}MB exceeds maximum 10MB`);
    }

    // Check if file is empty
    if (file.size === 0) {
      errors.push('File cannot be empty');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Get suggested file upload tips
   */
  static getUploadTips(): string[] {
    return [
      'Ensure your CSV has a header row with column names',
      'Use standard delimiters (comma, semicolon, or tab)',
      'Keep file size under 10MB for optimal performance',
      'Remove special characters from column names',
      'Ensure consistent data types within columns'
    ];
  }
}