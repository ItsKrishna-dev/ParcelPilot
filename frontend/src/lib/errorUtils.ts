import { UserFacingError } from '../types/trust';

export function normalizeApiError(error: unknown): UserFacingError {
  if (typeof error === 'string') {
    if (
      error.includes('Failed to fetch') ||
      error.includes('NetworkError') ||
      error.includes('ECONNREFUSED')
    ) {
      return {
        title: 'Backend Service Unavailable',
        message:
          'Unable to connect to the ParcelPilot backend service. Please verify the FastAPI uvicorn server is running.',
        code: 'BACKEND_UNAVAILABLE',
      };
    }
    if (error.includes('403') || error.includes('Access denied')) {
      return {
        title: 'Access Restricted',
        message:
          'Access denied: you do not have permission to view this record or execute this action.',
        code: 'ACCESS_DENIED',
      };
    }
    return {
      title: 'System Error',
      message: error,
      code: 'UNKNOWN',
    };
  }

  if (error && typeof error === 'object') {
    const errObj = error as Record<string, any>;
    const msg = String(errObj.message || errObj.detail || '');

    if (
      msg.includes('Failed to fetch') ||
      msg.includes('NetworkError') ||
      msg.includes('ECONNREFUSED')
    ) {
      return {
        title: 'Backend Service Unavailable',
        message:
          'Unable to connect to the ParcelPilot backend service (http://127.0.0.1:8000). Please check server logs.',
        code: 'BACKEND_UNAVAILABLE',
      };
    }

    if (
      msg.includes('503') ||
      msg.includes('provider') ||
      msg.includes('Groq') ||
      msg.includes('NVIDIA')
    ) {
      return {
        title: 'AI Model Provider Unavailable',
        message:
          'Primary and fallback AI model providers are currently unreachable. The inquiry has been queued for support escalation.',
        code: 'PROVIDER_UNAVAILABLE',
      };
    }

    if (
      msg.includes('403') ||
      msg.includes('Access denied') ||
      msg.includes('Forbidden')
    ) {
      return {
        title: 'Access Restricted',
        message:
          'Access restricted: requested order, ticket, or contract data belongs to another account.',
        code: 'ACCESS_DENIED',
      };
    }

    if (
      msg.includes('422') ||
      msg.includes('validation') ||
      msg.includes('Invalid')
    ) {
      return {
        title: 'Validation Error',
        message:
          'The request parameter or message payload could not be validated.',
        code: 'VALIDATION_ERROR',
      };
    }

    if (msg.includes('timeout') || msg.includes('ETIMEDOUT')) {
      return {
        title: 'Request Timeout',
        message:
          'The request timed out while retrieving authoritative data sources.',
        code: 'TIMEOUT',
      };
    }

    if (msg.length > 0) {
      return {
        title: 'System Error',
        message: msg,
        code: 'UNKNOWN',
      };
    }
  }

  return {
    title: 'System Error',
    message:
      'An unexpected issue occurred while processing your request. Please try again.',
    code: 'UNKNOWN',
  };
}
