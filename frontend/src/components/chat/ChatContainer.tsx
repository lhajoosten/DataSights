/**
 * ChatContainer Component - Manages the conversation interface
 * 
 * This is the main chat component that handles the conversational interface
 * for asking questions about data. It's like a smart chatbot specifically
 * designed for data analysis.
 * 
 * Key Responsibilities:
 * 1. Display conversation history (user questions + AI responses)
 * 2. Handle user input and send questions to the backend
 * 3. Show loading states while AI processes questions
 * 4. Display errors and allow retries
 * 5. Manage suggested questions to help users get started
 * 
 * This component follows the "Container Component" pattern - it manages
 * state and coordinates between child components, while the child components
 * handle the actual UI rendering.
 */

import React from 'react';
// Import our custom UI components
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { ChatMessage } from './ChatMessage';        // Individual message display
import { ChatInput } from './ChatInput';            // Input box and suggestions
import { ErrorMessage } from '@/components/ui/ErrorMessage';   // Error handling
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'; // Loading state
// Import our custom hook for chat functionality
import { useChat } from '@/hooks/useChat';
// Import types for TypeScript safety
import { ChatStatus } from '@/types/app';
import { ChartData } from '@/types/api';

// TypeScript interface defines what props this component needs
interface ChatContainerProps {
  fileId: string;                                    // ID of uploaded CSV file
  onChartGenerated: (chartData: ChartData) => void; // Callback when chart is ready
  suggestedQuestions: string[];                      // Helpful question examples
  className?: string;                                // Optional CSS styling
}

// React Functional Component with TypeScript
export const ChatContainer: React.FC<ChatContainerProps> = ({
  fileId,
  onChartGenerated,
  suggestedQuestions,
  className,
}) => {
  // Custom hook handles all chat logic (state management, API calls, etc.)
  // This separates business logic from UI rendering (separation of concerns)
  const { 
    chatState,         // Current status (thinking, error, etc.)
    chatHistory,       // Array of all messages in conversation
    currentChart,      // Latest generated chart data
    askQuestion,       // Function to send questions to backend
    clearChat,         // Function to reset conversation
    retryLastQuestion  // Function to retry failed questions
  } = useChat();
  
  // React ref to automatically scroll to newest messages
  // useRef creates a mutable reference that persists across re-renders
  const chatEndRef = React.useRef<HTMLDivElement>(null);

  /**
   * Handle when user sends a message
   * 
   * This function gets called when the user submits a question.
   * It's an async function because sending the question to the backend
   * involves network requests that take time.
   */
  const handleSendMessage = async (message: string) => {
    // Call the askQuestion function from our custom hook
    // Pass the message and file ID so backend knows what data to analyze
    await askQuestion(message, fileId);
  };

  /**
   * Auto-scroll to bottom when new messages arrive
   * 
   * useEffect runs after the component renders. This particular effect
   * runs whenever chatHistory changes (new messages are added).
   * It automatically scrolls the chat to show the newest message.
   */
  React.useEffect(() => {
    // Scroll the chat container to show the latest message
    // scrollIntoView is a browser API that scrolls to make an element visible
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]); // Dependency array: effect runs when chatHistory changes

  /**
   * Notify parent component when a new chart is generated
   * 
   * This effect watches for changes to currentChart. When the backend
   * generates new chart data, we call the parent's onChartGenerated function
   * to let it know there's a new chart to display.
   */
  React.useEffect(() => {
    if (currentChart) {
      // Call the callback function passed down from parent component
      onChartGenerated(currentChart);
    }
  }, [currentChart, onChartGenerated]); // Run when currentChart or callback changes

  return (
    <div className={className}>
      {/* Card component provides consistent styling and layout */}
      <Card>
        <CardHeader 
          title="Ask Questions About Your Data"
          subtitle="Use natural language to explore your data and generate visualizations"
        />
        <CardContent>
          <div className="space-y-4">
            
            {/* CHAT HISTORY SECTION */}
            {/* This div contains all the conversation messages */}
            <div className="min-h-[200px] max-h-[400px] overflow-y-auto space-y-4 p-4 bg-gray-50 rounded-lg">
              
              {/* EMPTY STATE: Show when no conversation yet */}
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
                // CONVERSATION STATE: Show all messages
                <>
                  {/* Render each message in the conversation history */}
                  {chatHistory.map((message, index) => (
                    <ChatMessage 
                      key={index}      // React needs unique keys for list items
                      message={message} // Pass the message data to child component
                    />
                  ))}
                  
                  {/* LOADING STATE: Show when AI is processing */}
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