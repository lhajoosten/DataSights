/**
 * Upload container component managing upload state and flow.
 * Similar to smart components in Angular with state management.
 */

import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { FileDropzone } from './FileDropZone';
import { UploadProgress } from './UploadProgress';
import { CSVPreview } from './CsvPreview';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { useCSVUpload } from '@/hooks/useCSVUpload';
import { UploadStatus } from '@/types/app';
import { CSVPreviewResponse } from '@/types/api';

interface UploadContainerProps {
  onUploadSuccess: (data: CSVPreviewResponse) => void;
  className?: string;
}

export const UploadContainer: React.FC<UploadContainerProps> = ({
  onUploadSuccess,
  className,
}) => {
  const { uploadState, uploadedFile, uploadCSV, clearUpload } = useCSVUpload();

  const handleFileSelect = async (file: File) => {
    await uploadCSV(file);
  };

  const handleRetry = () => {
    clearUpload();
  };

  // Notify parent when upload succeeds
  React.useEffect(() => {
    if (uploadState.status === UploadStatus.Success && uploadedFile) {
      onUploadSuccess(uploadedFile);
    }
  }, [uploadState.status, uploadedFile, onUploadSuccess]);

  return (
    <div className={className}>
      {uploadState.status === UploadStatus.Idle && (
        <Card>
          <CardHeader 
            title="Upload Your CSV File"
            subtitle="Upload a CSV file to start analyzing your data with natural language questions"
          />
          <CardContent>
            <FileDropzone
              onFileSelect={handleFileSelect}
              uploadStatus={uploadState.status}
            />
            
            <div className="mt-4 text-sm text-gray-600">
              <h4 className="font-medium mb-2">Tips for best results:</h4>
              <ul className="list-disc list-inside space-y-1">
                <li>Ensure your CSV has clear column headers</li>
                <li>Use consistent data formats within columns</li>
                <li>Keep file size under 10MB for optimal performance</li>
                <li>Remove special characters from column names</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}

      {(uploadState.status === UploadStatus.Uploading || 
        uploadState.status === UploadStatus.Processing) && (
        <Card>
          <CardContent>
            <UploadProgress
              status={uploadState.status}
              progress={uploadState.progress}
              fileName="your-file.csv"
            />
          </CardContent>
        </Card>
      )}

      {uploadState.status === UploadStatus.Error && (
        <Card>
          <CardContent>
            <ErrorMessage
              error={uploadState.error || 'Upload failed'}
              onRetry={handleRetry}
              showRetry={true}
            />
          </CardContent>
        </Card>
      )}

      {uploadState.status === UploadStatus.Success && uploadedFile && (
        <CSVPreview data={uploadedFile} />
      )}
    </div>
  );
};