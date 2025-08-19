/**
 * File dropzone component for CSV uploads.
 * Similar to file upload components in Angular with drag-and-drop functionality.
 */

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { clsx } from 'clsx';
import { Upload, File, AlertCircle } from 'lucide-react';
import { UploadStatus } from '@/types/app';

interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  uploadStatus: UploadStatus;
  accept?: string;
  maxSize?: number;
  disabled?: boolean;
  className?: string;
}

export const FileDropzone: React.FC<FileDropzoneProps> = ({
  onFileSelect,
  uploadStatus,
  accept = '.csv',
  maxSize = 10 * 1024 * 1024, // 10MB
  disabled = false,
  className,
}) => {
  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    maxSize,
    multiple: false,
    disabled: disabled || uploadStatus === UploadStatus.Uploading,
  });

  const isLoading = uploadStatus === UploadStatus.Uploading;
  const hasError = uploadStatus === UploadStatus.Error;

  return (
    <div
      {...getRootProps()}
      className={clsx(
        'border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
        {
          'border-gray-300 hover:border-gray-400': !isDragActive && !hasError && !isLoading,
          'border-primary-400 bg-primary-50': isDragActive && !isDragReject,
          'border-red-400 bg-red-50': isDragReject || hasError,
          'border-gray-200 bg-gray-50 cursor-not-allowed': isLoading || disabled,
        },
        className
      )}
    >
      <input {...getInputProps()} />
      
      <div className="space-y-4">
        {isLoading ? (
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          </div>
        ) : hasError ? (
          <AlertCircle className="mx-auto h-8 w-8 text-red-500" />
        ) : (
          <Upload className="mx-auto h-8 w-8 text-gray-400" />
        )}
        
        <div>
          {isLoading ? (
            <p className="text-sm text-gray-600">Uploading your file...</p>
          ) : isDragActive ? (
            isDragReject ? (
              <p className="text-sm text-red-600">
                Only CSV files are allowed
              </p>
            ) : (
              <p className="text-sm text-primary-600">
                Drop your CSV file here
              </p>
            )
          ) : (
            <div>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-gray-500 mt-1">
                CSV files only, up to {Math.round(maxSize / (1024 * 1024))}MB
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};