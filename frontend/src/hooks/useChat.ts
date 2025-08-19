/**
 * Custom hook for chat functionality.
 * Similar to stateful services in Angular with reactive patterns.
 */

import { useState, useCallback, useRef } from 'react';
import { ChatService } from '@/services/chat.service';
import { ChatMessage, ChartData } from '@/types/api';
import { ChatStatus } from '@/types/app';

interface UseChatResult {
  chatState: {
    status: ChatStatus;
    error?: string;
    clarificationPrompt?: string;
    suggestedQuestions: string[];
  };
  chatHistory: ChatMessage[];
  currentChart?: ChartData;
  askQuestion: (question: string, fileId: string) => Promise<void>;
  clearChat: () => void;
  retryLastQuestion: () => Promise<void>;
}

export const useChat = (): UseChatResult => {
  const [chatState, setChatState] = useState({
    status: ChatStatus.Idle,
    error: undefined as string | undefined,
    clarificationPrompt: undefined as string | undefined,
    suggestedQuestions: [] as string[],
  });
  
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [currentChart, setCurrentChart] = useState<ChartData>();
  
  // Store last question for retry functionality
  const lastQuestionRef = useRef<{ question: string; fileId: string }>();

  const askQuestion = useCallback(async (question: string, fileId: string) => {
    // Store for potential retry
    lastQuestionRef.current = { question, fileId };

    // Add user message to history
    const userMessage: ChatMessage = {
      role: 'user',
      content: question,
      timestamp: new Date().toISOString()
    };

    setChatHistory(prev => [...prev, userMessage]);
    setChatState({
      status: ChatStatus.Thinking,
      error: undefined,
      clarificationPrompt: undefined,
      suggestedQuestions: [],
    });

    try {
      const response = await ChatService.askQuestion({
        file_id: fileId,
        question,
        context: chatHistory.slice(-4) // Send last 4 messages as context
      });

      if (response.success && response.data) {
        const { message, chart_data, requires_clarification, clarification_prompt, suggested_questions } = response.data;

        // Add assistant message to history
        setChatHistory(prev => [...prev, message]);

        if (requires_clarification) {
          setChatState({
            status: ChatStatus.NeedsClarification,
            error: undefined,
            clarificationPrompt: clarification_prompt,
            suggestedQuestions: suggested_questions,
          });
        } else {
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