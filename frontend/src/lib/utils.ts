import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency: string): string {
  const symbols: Record<string, string> = {
    NGN: '₦',
    USD: '$',
    EUR: '€',
    CAD: 'C$',
    MXN: 'MX$',
    GBP: '£',
  };
  const symbol = symbols[currency] || '';
  return `${symbol}${amount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getStatusVariant(status: string): 'success' | 'danger' | 'warning' | 'info' | 'neutral' {
  const map: Record<string, 'success' | 'danger' | 'warning' | 'info' | 'neutral'> = {
    READY: 'success',
    APPROVED: 'success',
    COMPLETED: 'success',
    PROCESSED: 'success',
    ACTIVE: 'success',
    SUFFICIENT: 'success',
    SAFE_TO_RUN: 'success',
    
    HIGH: 'danger',
    BLOCKED: 'danger',
    SHORTFALL: 'danger',
    FAILED: 'danger',
    SUSPENDED: 'danger',
    REJECTED: 'danger',
    
    MEDIUM: 'warning',
    REVIEW_REQUIRED: 'warning',
    KYC_ACTION_REQUIRED: 'warning',
    KYC_PENDING: 'warning',
    REVIEW: 'warning',
    LOW: 'warning',
    
    INVITED: 'info',
    LINKED: 'info',
    WALLET_PENDING: 'info',
    PROCESSING: 'info',
    VERIFIED: 'info',
    READY_FOR_REVIEW: 'info',
    
    DRAFT: 'neutral',
    VALIDATED: 'neutral',
    ON_HOLD: 'neutral',
  };
  
  return map[status] || 'neutral';
}
