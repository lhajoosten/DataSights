/**
 * Chat container component managing conversation state.
 * Similar to chat components in Angular applications with state management.
 */

import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useChat } from '@/hooks/useChat';
import { ChatStatus } from '@/types/app';
import { ChartData } from '@/types/api';

interface ChatContainerProps {
  fileId: string;
  onChartGenerated: (chartData: ChartData) => void;
  suggestedQuestions: string[];
  className?: string;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  fileId,
  onChartGenerated,
  suggestedQuestions,
  className,
}) => {
  const { chatState, chatHistory, currentChart, askQuestion, clearChat, retryLastQuestion } = useChat();
  const chatEndRef = React.useRef<HTMLDivElement>(null);

  const handleSendMessage = async (message: string) => {
    await askQuestion(message, fileId);
  };

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // Notify parent when chart is generated
  React.useEffect(() => {
    if (currentChart) {
      onChartGenerated(currentChart);
    }
  }, [currentChart, onChartGenerated]);

  return (
    <div className={className}>
      <Card>
        <CardHeader 
          title="Ask Questions About Your Data"
          subtitle="Use natural language to explore your data and generate visualizations"
        />
        <CardContent>
          <div className="space-y-4">
            {/* Chat History */}
            <div className="min-h-[200px] max-h-[400px] overflow-y-auto space-y-4 p-4 bg-gray-50 rounded-lg">
              {chatHistory.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <p className="text-sm">
                    Start by asking a question about your data!
                  </p>
                  <p className="text-xs mt-2">
                    Try: "Show sales by month" or "Compare performance across regions"
                  </p>
                </div>
              ) : (
                <>
                  {chatHistory.map((message, index) => (
                    <ChatMessage 
                      key={index} 
                      message={message} 
                    />
                  ))}
                  
                  {/* Loading indicator when thinking */}
                  {chatState.status === ChatStatus.Thinking && (
                    <div className="flex justify-center py-4">
                      <LoadingSpinner 
                        message="Analyzing your question..." 
                        size="sm" 
                      />
                    </div>
                  )}
                </>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Error Message */}
            {chatState.status === ChatStatus.Error && chatState.error && (
              <ErrorMessage
                error={chatState.error}
                onRetry={retryLastQuestion}
                showRetry={true}
              />
            )}

            {/* Chat Input */}
            <ChatInput
              onSendMessage={handleSendMessage}
              suggestedQuestions={chatState.suggestedQuestions.length > 0 
                ? chatState.suggestedQuestions 
                : suggestedQuestions
              }
              status={chatState.status}
              clarificationPrompt={chatState.clarificationPrompt}
              disabled={!fileId}
            />

            {/* Clear Chat Button */}
            {chatHistory.length > 0 && (
              <div className="text-center">
                <button
                  onClick={clearChat}
                  className="text-sm text-gray-500 hover:text-gray-700 underline"
                >
                  Clear conversation
                </button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};