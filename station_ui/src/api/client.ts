/**
 * Axios HTTP client configuration for Station Service API.
 *
 * Note: The server now returns camelCase field names directly via Pydantic's
 * alias_generator, so no client-side transformation is needed.
 */

import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import type { ApiResponse, ErrorResponse } from '../types';

/**
 * API client instance configured for Station Service.
 */
// Determine API base URL based on environment
// In production (served from /ui), use absolute path; in dev, use relative
const getBaseUrl = (): string => {
  // Check if we're being served from /ui path (production)
  if (typeof window !== 'undefined' && window.location.pathname.startsWith('/ui')) {
    return '/api';  // Absolute path from root
  }
  return '/api';  // Development mode with proxy
};

export const apiClient: AxiosInstance = axios.create({
  baseURL: getBaseUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Custom API error with status code for proper handling.
 */
export interface ApiError {
  code: string;
  message: string;
  status?: number;
}

/**
 * Response interceptor to handle errors.
 * Note: No transformation needed - server returns camelCase directly.
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Server returns camelCase directly via Pydantic alias_generator
    return response;
  },
  (error: AxiosError<ErrorResponse>) => {
    const status = error.response?.status;
    const responseData = error.response?.data as Record<string, unknown> | undefined;

    // Check for structured error response (ApiResponse format)
    if (responseData?.error) {
      return Promise.reject({
        ...(responseData.error as object),
        status,
      } as ApiError);
    }

    // Check for FastAPI HTTPException format (detail field)
    if (responseData?.detail) {
      const detail = responseData.detail;
      // Extract meaningful message based on status code
      let code = 'API_ERROR';
      let message = typeof detail === 'string' ? detail : JSON.stringify(detail);

      if (status === 503) {
        code = 'SERVICE_UNAVAILABLE';
        // Backend connection error typically contains "Cannot connect to backend"
        if (message.includes('connect to backend') || message.includes('Backend')) {
          message = '백엔드 MES 서버에 연결할 수 없습니다.';
        }
      } else if (status === 401) {
        code = 'UNAUTHORIZED';
      }

      return Promise.reject({
        code,
        message,
        status,
      } as ApiError);
    }

    if (error.code === 'ECONNABORTED') {
      return Promise.reject({
        code: 'TIMEOUT',
        message: '요청 시간이 초과되었습니다.',
        status,
      } as ApiError);
    }

    if (error.code === 'ERR_NETWORK' || !error.response) {
      return Promise.reject({
        code: 'NETWORK_ERROR',
        message: '서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.',
      } as ApiError);
    }

    // Handle specific HTTP status codes
    if (status === 503) {
      return Promise.reject({
        code: 'SERVICE_UNAVAILABLE',
        message: '서버에 연결할 수 없습니다.',
        status,
      } as ApiError);
    }

    return Promise.reject({
      code: 'UNKNOWN_ERROR',
      message: error.message || '알 수 없는 오류가 발생했습니다.',
      status,
    } as ApiError);
  }
);

/**
 * Helper to extract data from API response.
 */
export function extractData<T>(response: AxiosResponse<ApiResponse<T>>): T {
  return response.data.data;
}

export default apiClient;
