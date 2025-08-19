/**
 * Main application component.
 * Similar to AppComponent in Angular with routing and state management.
 */

import React, { useState } from 'react';
import { UploadContainer } from '@/components/upload/UploadContainer';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { ChartRenderer } from '@/components/chart/ChartRenderer';
import { Button } from '@/components/ui/Button';
import { CSVPreviewResponse, ChartData } from '@/types/api';
import { ChatService } from '@/services/chat.service';
import { FileText, MessageSquare, BarChart3, RotateCcw } from 'lucide-react';

// Application state enum
enum AppStep {
  Upload = 'upload',
  Analysis = 'analysis',
}

function App() {
  const [currentStep, setCurrentStep] = useState<AppStep>(AppStep.Upload);
  const [uploadedFile, setUploadedFile] = useState<CSVPreviewResponse>();
  const [currentChart, setCurrentChart] = useState<ChartData>();

  const handleUploadSuccess = (data: CSVPreviewResponse) => {
    setUploadedFile(data);
    setCurrentStep(AppStep.Analysis);
  };

  const handleChartGenerated = (chartData: ChartData) => {
    setCurrentChart(chartData);
  };

  const handleStartOver = () => {
    setCurrentStep(AppStep.Upload);
    setUploadedFile(undefined);
    setCurrentChart(undefined);
  };

  const getSuggestedQuestions = (): string[] => {
    if (!uploadedFile) return [];
    return ChatService.generateSuggestedQuestions(uploadedFile.column_info);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <BarChart3 className="h-8 w-8 text-primary-600" />
              <h1 className="text-xl font-semibold text-gray-900">
                Talk to Your Data
              </h1>
            </div>
            
            {currentStep === AppStep.Analysis && (
              <Button
                variant="outline"
                onClick={handleStartOver}
                className="flex items-center space-x-2"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Start Over</span>
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Progress Steps */}
        <div className="mb-8">
          <nav aria-label="Progress">
            <ol className="flex items-center">
              <li className="relative">
                <div className={`flex items-center space-x-2 ${
                  currentStep === AppStep.Upload ? 'text-primary-600' : 'text-green-600'
                }`}>
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                    currentStep === AppStep.Upload 
                      ? 'border-primary-600 bg-primary-600 text-white'
                      : 'border-green-600 bg-green-600 text-white'
                  }`}>
                    <FileText className="h-4 w-4" />
                  </div>
                  <span className="text-sm font-medium">Upload CSV</span>
                </div>
              </li>

              <div className="flex-1 mx-4">
                <div className={`h-0.5 ${
                  currentStep === AppStep.Analysis ? 'bg-primary-600' : 'bg-gray-300'
                }`} />
              </div>

              <li className="relative">
                <div className={`flex items-center space-x-2 ${
                  currentStep === AppStep.Analysis ? 'text-primary-600' : 'text-gray-500'
                }`}>
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                    currentStep === AppStep.Analysis
                      ? 'border-primary-600 bg-primary-600 text-white'
                      : 'border-gray-300 bg-white text-gray-500'
                  }`}>
                    <MessageSquare className="h-4 w-4" />
                  </div>
                  <span className="text-sm font-medium">Analyze Data</span>
                </div>
              </li>
            </ol>
          </nav>
        </div>

        {/* Step Content */}
        {currentStep === AppStep.Upload && (
          <UploadContainer 
            onUploadSuccess={handleUploadSuccess}
            className="max-w-4xl mx-auto"
          />
        )}

        {currentStep === AppStep.Analysis && uploadedFile && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Chat Section */}
            <div className="space-y-6">
              <ChatContainer
                fileId={uploadedFile.file_id}
                onChartGenerated={handleChartGenerated}
                suggestedQuestions={getSuggestedQuestions()}
              />
            </div>

            {/* Chart Section */}
            <div className="space-y-6">
              {currentChart ? (
                <ChartRenderer chartData={currentChart} />
              ) : (
                <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
                  <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Visualization Yet
                  </h3>
                  <p className="text-gray-600">
                    Ask a question about your data to generate a chart
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-500">
            <p>
              Upload CSV files and ask natural language questions to generate visualizations.
              Built with React, TypeScript, and FastAPI.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;