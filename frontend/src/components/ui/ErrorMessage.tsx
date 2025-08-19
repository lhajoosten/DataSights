/**
 * Error message component with retry functionality.
 * Similar to error handling components in Angular applications.
 */

import React from 'react';
import { clsx } from 'clsx';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';
import { ErrorProps } from '@/types/app';
import { ApiError } from '@/types/api';

export const ErrorMessage: React.FC<ErrorProps> = ({
  error,
  onRetry,
  showRetry = true,
  className,
}) => {
  const getErrorMessage = (error: string | ApiError): string => {
    if (typeof error === 'string') {
      return error;
    }
    return error.message || 'An unexpected error occurred';
  };

  const getErrorDetails = (error: string | ApiError): string | undefined => {
    if (typeof error === 'object' && error.details) {
      return JSON.stringify(error.details, null, 2);
    }
    return undefined;
  };

  return (
    <div className={clsx('bg-red-50 border border-red-200 rounded-md p-4', className)}>
      <div className="flex items-start">
        <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5" />
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">
            Error
          </h3>
          <p className="text-sm text-red-700 mt-1">
            {getErrorMessage(error)}
          </p>
          
          {getErrorDetails(error) && (
            <details className="mt-2">
              <summary className="text-xs text-red-600 cursor-pointer">
                Technical Details
              </summary>
              <pre className="text-xs text-red-600 mt-1 bg-red-100 p-2 rounded overflow-auto">
                {getErrorDetails(error)}
              </pre>
            </details>
          )}
          
          {showRetry && onRetry && (
            <div className="mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="text-red-700 border-red-300 hover:bg-red-100"
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Retry
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};