/**
 * Upload progress component with status indicators.
 * Similar to progress indicators in Angular Material.
 */

import React from 'react';
import { clsx } from 'clsx';
import { CheckCircle, XCircle, Upload } from 'lucide-react';
import { UploadStatus } from '@/types/app';

interface UploadProgressProps {
  status: UploadStatus;
  progress: number;
  fileName?: string;
  error?: string;
  className?: string;
}

export const UploadProgress: React.FC<UploadProgressProps> = ({
  status,
  progress,
  fileName,
  error,
  className,
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case UploadStatus.Success:
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case UploadStatus.Error:
        return <XCircle className="h-5 w-5 text-red-500" />;
      case UploadStatus.Uploading:
        return <Upload className="h-5 w-5 text-primary-500" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case UploadStatus.Uploading:
        return `Uploading... ${progress}%`;
      case UploadStatus.Processing:
        return 'Processing file...';
      case UploadStatus.Success:
        return 'Upload completed successfully';
      case UploadStatus.Error:
        return error || 'Upload failed';
      default:
        return '';
    }
  };

  const getProgressBarColor = () => {
    switch (status) {
      case UploadStatus.Success:
        return 'bg-green-500';
      case UploadStatus.Error:
        return 'bg-red-500';
      default:
        return 'bg-primary-500';
    }
  };

  if (status === UploadStatus.Idle) {
    return null;
  }

  return (
    <div className={clsx('space-y-3', className)}>
      <div className="flex items-center space-x-3">
        {getStatusIcon()}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {fileName}
          </p>
          <p className="text-sm text-gray-500">
            {getStatusText()}
          </p>
        </div>
      </div>

      {(status === UploadStatus.Uploading || status === UploadStatus.Processing) && (
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={clsx('h-2 rounded-full transition-all duration-300', getProgressBarColor())}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
};