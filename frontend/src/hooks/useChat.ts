/**
 * useChat Custom Hook - Manages chat state and interactions
 * 
 * This is a "custom hook" - a reusable piece of logic that manages
 * the complex state needed for our chat functionality. Custom hooks
 * are a React pattern for sharing stateful logic between components.
 * 
 * Why use a custom hook?
 * 1. Separation of Concerns: Keeps business logic separate from UI
 * 2. Reusability: Can be used in multiple components
 * 3. Testability: Logic can be tested independently
 * 4. Readability: Components focus on rendering, hooks handle state
 * 
 * This hook manages:
 * - Conversation history (messages back and forth)
 * - Chat status (idle, thinking, error, etc.)
 * - API calls to backend
 * - Error handling and retry logic
 * - Context management for follow-up questions
 */

import { useState, useCallback, useRef } from 'react';
import { ChatService } from '@/services/chat.service';  // API service
import { ChatMessage, ChartData } from '@/types/api';   // Type definitions
import { ChatStatus } from '@/types/app';               // Status enums

// TypeScript interface defines what this hook returns
// This makes it clear what functionality is available to components using this hook
interface UseChatResult {
  chatState: {
    status: ChatStatus;           // Current status (idle, thinking, error, etc.)
    error?: string;              // Error message if something went wrong
    clarificationPrompt?: string; // When AI needs more info from user
    suggestedQuestions: string[]; // Helpful question suggestions
  };
  chatHistory: ChatMessage[];    // All messages in conversation
  currentChart?: ChartData;      // Latest generated chart data
  askQuestion: (question: string, fileId: string) => Promise<void>; // Send question function
  clearChat: () => void;         // Reset conversation function
  retryLastQuestion: () => Promise<void>; // Retry failed question function
}

/**
 * The main custom hook function
 * 
 * This function encapsulates all the chat logic and returns an object
 * with state and functions that components can use.
 */
export const useChat = (): UseChatResult => {
  // STATE MANAGEMENT using React's useState hook
  
  // Track the current status of the chat (idle, thinking, error, etc.)
  const [chatState, setChatState] = useState({
    status: ChatStatus.Idle,                    // Start in idle state
    error: undefined as string | undefined,     // No error initially
    clarificationPrompt: undefined as string | undefined, // No clarification needed initially
    suggestedQuestions: [] as string[],         // Empty suggestions initially
  });
  
  // Store all messages in the conversation
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  
  // Store the current chart data (when AI generates a chart)
  const [currentChart, setCurrentChart] = useState<ChartData>();
  
  // Use useRef to store data that persists across re-renders but doesn't trigger re-renders
  // This stores the last question for retry functionality
  const lastQuestionRef = useRef<{ question: string; fileId: string }>();

  /**
   * Send a question to the AI and handle the response
   * 
   * useCallback wraps this function to prevent unnecessary re-renders.
   * It only recreates the function if chatHistory changes.
   * 
   * This function:
   * 1. Adds user message to chat history
   * 2. Sets status to "thinking"
   * 3. Calls the backend API
   * 4. Handles the response (success, error, or clarification needed)
   * 5. Updates the UI state accordingly
   */
  const askQuestion = useCallback(async (question: string, fileId: string) => {
    // Store this question in case we need to retry it later
    lastQuestionRef.current = { question, fileId };

    // Create a user message object with current timestamp
    const userMessage: ChatMessage = {
      role: 'user',               // Mark as user message (vs assistant)
      content: question,          // The actual question text
      timestamp: new Date().toISOString() // ISO timestamp for sorting
    };

    // Add user message to chat history
    // We use the functional update pattern (prev => ...) to ensure we get the latest state
    setChatHistory(prev => [...prev, userMessage]);
    
    // Update chat status to show we're processing
    setChatState({
      status: ChatStatus.Thinking,   // Show loading state
      error: undefined,              // Clear any previous errors
      clarificationPrompt: undefined, // Clear any previous clarification requests
      suggestedQuestions: [],        // Clear suggestions (will get new ones from response)
    });

    try {
      // Make API call to backend
      // We send the question, file ID, and recent conversation context
      const response = await ChatService.askQuestion({
        file_id: fileId,
        question,
        context: chatHistory.slice(-4) // Send last 4 messages for context (follow-up questions)
      });

      // Handle successful API response
      if (response.success && response.data) {
        // Destructure the response data
        const { 
          message,               // AI's response message
          chart_data,           // Generated chart data (if any)
          requires_clarification, // Does AI need more info?
          clarification_prompt,  // What clarification does AI need?
          suggested_questions   // Helpful question suggestions
        } = response.data;

        // Add the AI's response message to chat history
        setChatHistory(prev => [...prev, message]);

        // Handle different response types
        if (requires_clarification) {
          // AI needs more information from the user
          setChatState({
            status: ChatStatus.NeedsClarification,
            error: undefined,
            clarificationPrompt: clarification_prompt,
            suggestedQuestions: suggested_questions,
          });
        } else {
          // Successful response with chart data
          setChatState({
            status: ChatStatus.Success,
            error: undefined,
            clarificationPrompt: undefined,
            suggestedQuestions: suggested_questions,
          });

          // Update current chart if provided
          if (chart_data) {
            setCurrentChart(chart_data);
          }
        }
      } else {
        setChatState({
          status: ChatStatus.Error,
          error: response.error?.message || 'Failed to process question',
          clarificationPrompt: undefined,
          suggestedQuestions: [],
        });
      }
    } catch (error) {
      setChatState({
        status: ChatStatus.Error,
        error: error instanceof Error ? error.message : 'Failed to process question',
        clarificationPrompt: undefined,
        suggestedQuestions: [],
      });
    }
  }, [chatHistory]);

  const retryLastQuestion = useCallback(async () => {
    if (lastQuestionRef.current) {
      const { question, fileId } = lastQuestionRef.current;
      await askQuestion(question, fileId);
    }
  }, [askQuestion]);

  const clearChat = useCallback(() => {
    setChatHistory([]);
    setCurrentChart(undefined);
    setChatState({
      status: ChatStatus.Idle,
      error: undefined,
      clarificationPrompt: undefined,
      suggestedQuestions: [],
    });
    lastQuestionRef.current = undefined;
  }, []);

  return {
    chatState,
    chatHistory,
    currentChart,
    askQuestion,
    clearChat,
    retryLastQuestion
  };
};