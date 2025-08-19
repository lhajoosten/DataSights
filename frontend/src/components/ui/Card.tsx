/**
 * Reusable Card component for content organization.
 * Similar to mat-card in Angular Material.
 */

import React from 'react';
import { clsx } from 'clsx';
import { BaseComponentProps } from '@/types/app';

interface CardProps extends BaseComponentProps {
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  padding = 'md',
  shadow = 'sm',
  className,
  children,
}) => {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8',
  };

  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
  };

  return (
    <div
      className={clsx(
        'bg-white rounded-lg border border-gray-200',
        paddingClasses[padding],
        shadowClasses[shadow],
        className
      )}
    >
      {children}
    </div>
  );
};

interface CardHeaderProps extends BaseComponentProps {
  title?: string;
  subtitle?: string;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  subtitle,
  className,
  children,
}) => {
  return (
    <div className={clsx('border-b border-gray-200 pb-4 mb-4', className)}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      )}
      {subtitle && (
        <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
      )}
      {children}
    </div>
  );
};

export const CardContent: React.FC<BaseComponentProps> = ({
  className,
  children,
}) => {
  return (
    <div className={clsx('', className)}>
      {children}
    </div>
  );
};