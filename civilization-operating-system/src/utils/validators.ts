/**
 * Input Validation Functions
 * @author Fatih Dinc
 * @copyright 2026 Fatih Dinc
 * @license SEE LICENSE FILE
 */

import { ValidationError, MissingFieldError, RangeError } from './errors';
import type { Transaction } from '../core/riba-detector';

/**
 * Validates a transaction object
 */
export function validateTransaction(tx: Partial<Transaction>): Transaction {
  // Check required fields
  if (tx.amount === undefined || tx.amount === null) {
    throw new MissingFieldError('amount');
  }

  if (tx.profit_loss_sharing === undefined) {
    throw new MissingFieldError('profit_loss_sharing');
  }

  if (tx.time_based_interest === undefined) {
    throw new MissingFieldError('time_based_interest');
  }

  if (!tx.risk_distribution) {
    throw new MissingFieldError('risk_distribution');
  }

  // Validate amount
  if (typeof tx.amount !== 'number' || isNaN(tx.amount)) {
    throw new ValidationError('Amount must be a valid number', 'amount');
  }

  if (tx.amount < 0) {
    throw new RangeError('amount', 0);
  }

  // Validate risk_distribution
  if (tx.risk_distribution !== 'symmetric' && tx.risk_distribution !== 'asymmetric') {
    throw new ValidationError(
      'Risk distribution must be either "symmetric" or "asymmetric"',
      'risk_distribution'
    );
  }

  return tx as Transaction;
}

/**
 * Validates wealth amount for Zakāt calculation
 */
export function validateWealth(wealth: number): number {
  if (wealth === undefined || wealth === null) {
    throw new MissingFieldError('wealth');
  }

  if (typeof wealth !== 'number' || isNaN(wealth)) {
    throw new ValidationError('Wealth must be a valid number', 'wealth');
  }

  if (wealth < 0) {
    throw new RangeError('wealth', 0);
  }

  return wealth;
}

/**
 * Validates Nisab threshold
 */
export function validateNisab(nisab: number): number {
  if (nisab === undefined || nisab === null) {
    throw new MissingFieldError('nisab_threshold');
  }

  if (typeof nisab !== 'number' || isNaN(nisab)) {
    throw new ValidationError('Nisab must be a valid number', 'nisab_threshold');
  }

  if (nisab <= 0) {
    throw new RangeError('nisab_threshold', 0.01);
  }

  return nisab;
}

/**
 * Validates category string
 */
export function validateCategory(category: string): string {
  if (!category) {
    throw new MissingFieldError('category');
  }

  if (typeof category !== 'string') {
    throw new ValidationError('Category must be a string', 'category');
  }

  if (category.trim().length === 0) {
    throw new ValidationError('Category cannot be empty', 'category');
  }

  return category.trim().toLowerCase();
}

/**
 * Sanitizes string input
 */
export function sanitizeString(input: string): string {
  if (typeof input !== 'string') {
    return '';
  }
  
  return input
    .trim()
    .replace(/[<>]/g, '') // Remove potential HTML tags
    .substring(0, 1000); // Limit length
}
