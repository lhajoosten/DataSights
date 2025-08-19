/**
 * Individual chat message component.
 * Similar to chat message components in messaging applications.
 */

import React from 'react';
import { clsx } from 'clsx';
import { User, Bot } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '@/types/api';

interface ChatMessageProps {
  message: ChatMessageType;
  className?: string;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  className,
}) => {
  const isUser = message.role === 'user';
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={clsx('flex space-x-3', className)}>
      <div className={clsx(
        'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
        {
          'bg-primary-100': isUser,
          'bg-gray-100': !isUser,
        }
      )}>
        {isUser ? (
          <User className="h-4 w-4 text-primary-600" />
        ) : (
          <Bot className="h-4 w-4 text-gray-600" />
        )}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <p className="text-sm font-medium text-gray-900">
            {isUser ? 'You' : 'Assistant'}
          </p>
          <p className="text-xs text-gray-500">
            {formatTime(message.timestamp)}
          </p>
        </div>
        
        <div className={clsx(
          'mt-1 p-3 rounded-lg text-sm',
          {
            'bg-primary-50 text-primary-900': isUser,
            'bg-gray-50 text-gray-900': !isUser,
          }
        )}>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    </div>
  );
};