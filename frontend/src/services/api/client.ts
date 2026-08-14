import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { ApiError, ApiResponse } from '@/types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else if (token) {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

// Request Interceptor: Attach Access Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

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

    // Handle 401 Token Expiration & Refresh Flow
    if (status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken && !originalRequest.url?.includes('/auth/login') && !originalRequest.url?.includes('/auth/refresh')) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then((token) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`;
              }
              return apiClient(originalRequest);
            })
            .catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          const res = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const responseData = res.data?.data || res.data;
          const newToken = responseData.access_token;
          const newRefreshToken = responseData.refresh_token;

          localStorage.setItem('access_token', newToken);
          if (newRefreshToken) {
            localStorage.setItem('refresh_token', newRefreshToken);
          }

          processQueue(null, newToken);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          }
          return apiClient(originalRequest);
        } catch (refreshErr) {
          processQueue(refreshErr, null);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
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
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.dispatchEvent(new Event('auth:unauthorized'));
      }
    }

    // Standardized Error Parsing for 403, 404, 409, 422, 500
    let errorMessage = 'An unexpected error occurred.';
    let validationErrors: Record<string, string> | null = null;

    if (data) {
      if (typeof data === 'object') {
        errorMessage = data.message || data.detail || errorMessage;
        if (data.errors && typeof data.errors === 'object') {
          validationErrors = data.errors;
        }
      } else if (typeof data === 'string') {
        errorMessage = data;
      }
    }

    if (status === 403) {
      errorMessage = errorMessage || 'You do not have permission to access this resource.';
    } else if (status === 404) {
      errorMessage = errorMessage || 'The requested resource was not found.';
    } else if (status === 409) {
      errorMessage = errorMessage || 'A conflict occurred with the current state.';
    } else if (status === 500) {
      errorMessage = 'Internal server error. Please contact your administrator.';
    }

    const formattedErr: ApiError = {
      message: errorMessage,
      status: status,
      errors: validationErrors,
    };

    return Promise.reject(formattedErr);
  }
);
