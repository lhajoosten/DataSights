/**
 * Chat input component with suggested questions.
 * Similar to message input components with auto-suggestions.
 */

import React, { useState, useRef, useEffect } from 'react';
import { clsx } from 'clsx';
import { Send, Lightbulb } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { ChatStatus } from '@/types/app';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  suggestedQuestions: string[];
  status: ChatStatus;
  clarificationPrompt?: string;
  disabled?: boolean;
  className?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  suggestedQuestions,
  status,
  clarificationPrompt,
  disabled = false,
  className,
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isLoading = status === ChatStatus.Thinking;
  const isDisabled = disabled || isLoading;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isDisabled) {
      onSendMessage(trimmedMessage);
      setMessage('');
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    if (!isDisabled) {
      onSendMessage(question);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Clarification Prompt */}
      {clarificationPrompt && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <Lightbulb className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-800">
                I need more information
              </p>
              <p className="text-sm text-yellow-700 mt-1">
                {clarificationPrompt}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Suggested Questions */}
      {suggestedQuestions.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">
            Suggested Questions
          </p>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuestion(question)}
                disabled={isDisabled}
                className={clsx(
                  'px-3 py-1.5 text-sm rounded-full border transition-colors',
                  'hover:bg-primary-50 hover:border-primary-300 hover:text-primary-700',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'border-gray-300 text-gray-700 bg-white'
                )}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Message Input */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isLoading 
                ? "Thinking..." 
                : "Ask a question about your data (e.g., 'Show sales by month')"
            }
            disabled={isDisabled}
            rows={1}
            className={clsx(
              'w-full resize-none rounded-lg border border-gray-300 px-4 py-3 pr-12',
              'focus:border-primary-500 focus:ring-1 focus:ring-primary-500',
              'disabled:bg-gray-100 disabled:cursor-not-allowed',
              'text-sm placeholder-gray-500'
            )}
            style={{ minHeight: '48px', maxHeight: '120px' }}
          />
          
          <div className="absolute bottom-2 right-2">
            <Button
              type="submit"
              size="sm"
              disabled={isDisabled || !message.trim()}
              loading={isLoading}
              className="rounded-full w-8 h-8 p-0"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>Press Enter to send, Shift+Enter for new line</span>
          <span>{message.length}/1000</span>
        </div>
      </form>
    </div>
  );
};