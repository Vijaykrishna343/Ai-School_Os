import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { ApiError, ApiResponse } from '@/types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: () => void;
  reject: (err: any) => void;
}> = [];

const processQueue = (error: any) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve();
    }
  });
  failedQueue = [];
};

// Response Interceptor: Envelope Handling & 401 Refresh
apiClient.interceptors.response.use(
  (response) => {
    // If backend returns envelope format { success, message, data, errors }
    const body = response.data;
    if (body && typeof body === 'object' && 'success' in body) {
      if (!body.success) {
        const apiErr: ApiError = {
          message: body.message || 'Operation failed',
          status: response.status,
          errors: body.errors || null,
        };
        return Promise.reject(apiErr);
      }
      return body.data !== undefined ? body.data : body;
    }
    return body;
  },
  async (error: AxiosError<any>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (!error.response) {
      const netErr: ApiError = {
        message: 'Unable to connect to AI School OS backend server.',
        status: 0,
      };
      return Promise.reject(netErr);
    }

    const { status, data } = error.response;

    // Handle 401 Token Expiration & Refresh Flow using HttpOnly cookies
    if (status === 401 && !originalRequest._retry) {
      if (!originalRequest.url?.includes('/auth/login') && !originalRequest.url?.includes('/auth/refresh')) {
        if (isRefreshing) {
          return new Promise<void>((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then(() => apiClient(originalRequest))
            .catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          await axios.post(`${BASE_URL}/auth/refresh`, {}, { withCredentials: true });
          processQueue(null);
          return apiClient(originalRequest);
        } catch (refreshErr) {
          processQueue(refreshErr);
          window.dispatchEvent(new Event('auth:unauthorized'));
          const authErr: ApiError = {
            message: 'Session expired. Please log in again.',
            status: 401,
          };
          return Promise.reject(authErr);
        } finally {
          isRefreshing = false;
        }
      } else {
        window.dispatchEvent(new Event('auth:unauthorized'));
      }
    }

    // Standardized Error Parsing for 400, 401, 403, 404, 409, 422, 500
    let errorMessage = 'An unexpected error occurred.';
    let validationErrors: Record<string, string> | null = null;

    if (data) {
      if (typeof data === 'object') {
        const rawMessage = data.error?.message || data.message || data.detail;
        if (typeof rawMessage === 'string' && rawMessage.trim()) {
          errorMessage = rawMessage;
        } else if (Array.isArray(data.detail)) {
          // Format FastAPI / Pydantic validation error array
          const messages = data.detail.map((err: any) => {
            if (typeof err === 'string') return err;
            if (err && typeof err === 'object') {
              const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : '';
              const msg = err.msg || 'invalid value';
              return field ? `${field}: ${msg}` : msg;
            }
            return 'validation error';
          });
          errorMessage = messages.join('; ') || 'Validation failed.';
        } else if (data.detail && typeof data.detail === 'object') {
          errorMessage = JSON.stringify(data.detail);
        }

        if (data.errors && typeof data.errors === 'object' && !Array.isArray(data.errors)) {
          validationErrors = data.errors;
        }
      } else if (typeof data === 'string' && data.trim()) {
        errorMessage = data;
      }
    }

    if (status === 403) {
      errorMessage = errorMessage !== 'An unexpected error occurred.' ? errorMessage : 'You do not have permission to access this resource.';
    } else if (status === 404) {
      errorMessage = errorMessage !== 'An unexpected error occurred.' ? errorMessage : 'The requested resource was not found.';
    } else if (status === 409) {
      errorMessage = errorMessage !== 'An unexpected error occurred.' ? errorMessage : 'A conflict occurred with the current state.';
    } else if (status === 500) {
      errorMessage = 'Internal server error. Please contact your administrator.';
    }

    const correlationId = 
      (error.response?.headers && (error.response.headers['x-correlation-id'] || error.response.headers['x-request-id']))
      || data?.error?.correlation_id;

    const formattedErr: ApiError = {
      message: errorMessage,
      status: status,
      errors: validationErrors,
      correlationId: correlationId,
    };

    return Promise.reject(formattedErr);
  }
);

