import React from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps {
  variant?: 'success' | 'danger' | 'warning' | 'info' | 'neutral';
  size?: 'sm' | 'md';
  children: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  size = 'sm',
  children,
  className,
  icon,
}) => {
  const variants = {
    success: 'bg-success-bg text-success-text border-success/20',
    danger: 'bg-danger-bg text-danger-text border-danger/20',
    warning: 'bg-warning-bg text-warning-text border-warning/20',
    info: 'bg-info-bg text-info-text border-info/20',
    neutral: 'bg-canvas-subtle text-text-muted border-border',
  };
  
  const sizes = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
  };
  
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-medium rounded-md border',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {icon}
      {children}
    </span>
  );
};
