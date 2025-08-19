/**
 * CSV preview component showing data table and metadata.
 * Similar to data table components in Angular Material.
 */

import React from 'react';
import { clsx } from 'clsx';
import { FileText, Database, Clock } from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { CSVPreviewResponse } from '@/types/api';

interface CSVPreviewProps {
  data: CSVPreviewResponse;
  className?: string;
}

export const CSVPreview: React.FC<CSVPreviewProps> = ({
  data,
  className,
}) => {
  const formatFileSize = (sizeInMB: number): string => {
    if (sizeInMB < 1) {
      return `${Math.round(sizeInMB * 1024)} KB`;
    }
    return `${sizeInMB.toFixed(2)} MB`;
  };

  const getColumnTypeIcon = (type: string) => {
    switch (type) {
      case 'integer':
      case 'float':
        return '🔢';
      case 'datetime':
      case 'date':
        return '📅';
      case 'boolean':
        return '☑️';
      default:
        return '📝';
    }
  };

  return (
    <div className={clsx('space-y-6', className)}>
      {/* File Metadata */}
      <Card>
        <CardHeader title="File Information" />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900">Filename</p>
                <p className="text-sm text-gray-600 truncate">{data.filename}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Database className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900">Size</p>
                <p className="text-sm text-gray-600">
                  {formatFileSize(data.file_size_mb)} • {data.rows_total.toLocaleString()} rows • {data.columns_total} columns
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900">Status</p>
                <p className="text-sm text-green-600">Ready for analysis</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Column Information */}
      <Card>
        <CardHeader 
          title="Column Types" 
          subtitle={`Detected ${Object.keys(data.column_info).length} columns with their data types`}
        />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(data.column_info).map(([column, type]) => (
              <div
                key={column}
                className="flex items-center space-x-2 p-2 bg-gray-50 rounded-md"
              >
                <span className="text-lg" role="img" aria-label={type}>
                  {getColumnTypeIcon(type)}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {column}
                  </p>
                  <p className="text-xs text-gray-500 capitalize">
                    {type}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Data Preview Table */}
      <Card>
        <CardHeader 
          title="Data Preview" 
          subtitle={`Showing first ${Math.min(data.preview_rows.length, 20)} rows`}
        />
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {Object.keys(data.column_info).map((column) => (
                    <th
                      key={column}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      <div className="flex items-center space-x-1">
                        <span>{column}</span>
                        <span className="text-gray-400" title={data.column_info[column]}>
                          {getColumnTypeIcon(data.column_info[column])}
                        </span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.preview_rows.map((row, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    {Object.keys(data.column_info).map((column) => (
                      <td
                        key={column}
                        className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate"
                        title={String(row[column] || '')}
                      >
                        {row[column] !== null && row[column] !== undefined 
                          ? String(row[column]) 
                          : (
                            <span className="text-gray-400 italic">null</span>
                          )
                        }
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {data.rows_total > data.preview_rows.length && (
            <div className="mt-4 text-center">
              <p className="text-sm text-gray-500">
                ... and {(data.rows_total - data.preview_rows.length).toLocaleString()} more rows
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};