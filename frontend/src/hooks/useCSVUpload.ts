/**
 * Custom hook for CSV upload functionality.
 * Similar to reactive services in Angular with state management.
 */

import { useState, useCallback } from 'react';
import { CSVService } from '@/services/csv.service';
import { CSVPreviewResponse } from '@/types/api';
import { UploadStatus } from '@/types/app';

interface UseCSVUploadResult {
  uploadState: {
    status: UploadStatus;
    progress: number;
    error?: string;
  };
  uploadedFile?: CSVPreviewResponse;
  uploadCSV: (file: File) => Promise<void>;
  clearUpload: () => void;
  validateFile: (file: File) => { isValid: boolean; errors: string[] };
}

export const useCSVUpload = (): UseCSVUploadResult => {
  const [uploadState, setUploadState] = useState({
    status: UploadStatus.Idle,
    progress: 0,
    error: undefined as string | undefined,
  });
  const [uploadedFile, setUploadedFile] = useState<CSVPreviewResponse>();

  const uploadCSV = useCallback(async (file: File) => {
    // Client-side validation first
    const validation = CSVService.validateFile(file);
    if (!validation.isValid) {
      setUploadState({
        status: UploadStatus.Error,
        progress: 0,
        error: validation.errors.join('; ')
      });
      return;
    }

    setUploadState({
      status: UploadStatus.Uploading,
      progress: 0,
      error: undefined
    });

    try {
      const response = await CSVService.uploadCSV(file, (progress) => {
        setUploadState(prev => ({
          ...prev,
          progress
        }));
      });

      if (response.success && response.data) {
        setUploadState({
          status: UploadStatus.Success,
          progress: 100,
          error: undefined
        });
        setUploadedFile(response.data);
      } else {
        setUploadState({
          status: UploadStatus.Error,
          progress: 0,
          error: response.error?.message || 'Upload failed'
        });
      }
    } catch (error) {
      setUploadState({
        status: UploadStatus.Error,
        progress: 0,
        error: error instanceof Error ? error.message : 'Upload failed'
      });
    }
  }, []);

  const clearUpload = useCallback(() => {
    setUploadState({
      status: UploadStatus.Idle,
      progress: 0,
      error: undefined
    });
    setUploadedFile(undefined);
  }, []);

  const validateFile = useCallback((file: File) => {
    return CSVService.validateFile(file);
  }, []);

  return {
    uploadState,
    uploadedFile,
    uploadCSV,
    clearUpload,
    validateFile
  };
};