/**
 * Custom Error Classes for COS Backend
 * @author Fatih Dinc
 * @copyright 2026 Fatih Dinc
 * @license SEE LICENSE FILE
 */

/**
 * Base error class for all COS-related errors
 */
export class COSError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500
  ) {
    super(message);
    this.name = 'COSError';
    Error.captureStackTrace(this, this.constructor);
  }
}

/**
 * Error thrown when Riba is detected in a transaction
 */
export class RibaDetectedError extends COSError {
  constructor(
    message: string,
    public readonly violationType: string
  ) {
    super(message, 'RIBA_DETECTED', 400);
    this.name = 'RibaDetectedError';
  }
}

/**
 * Error thrown when input validation fails
 */
export class ValidationError extends COSError {
  constructor(
    message: string,
    public readonly field?: string
  ) {
    super(message, 'VALIDATION_ERROR', 400);
    this.name = 'ValidationError';
  }
}

/**
 * Error thrown when a required field is missing
 */
export class MissingFieldError extends ValidationError {
  constructor(field: string) {
    super(`Required field missing: ${field}`, field);
    this.name = 'MissingFieldError';
  }
}

/**
 * Error thrown when a value is out of acceptable range
 */
export class RangeError extends ValidationError {
  constructor(
    field: string,
    min?: number,
    max?: number
  ) {
    const rangeMsg = min !== undefined && max !== undefined
      ? `Value must be between ${min} and ${max}`
      : min !== undefined
      ? `Value must be at least ${min}`
      : `Value must be at most ${max}`;
    
    super(`${field}: ${rangeMsg}`, field);
    this.name = 'RangeError';
  }
}

/**
 * Error thrown when Sharia compliance check fails
 */
export class ShariaComplianceError extends COSError {
  constructor(
    message: string,
    public readonly category: string,
    public readonly violations: string[]
  ) {
    super(message, 'SHARIA_COMPLIANCE_ERROR', 400);
    this.name = 'ShariaComplianceError';
  }
}

/**
 * Error thrown when configuration is invalid
 */
export class ConfigurationError extends COSError {
  constructor(message: string) {
    super(message, 'CONFIGURATION_ERROR', 500);
    this.name = 'ConfigurationError';
  }
}
