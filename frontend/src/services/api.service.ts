/**
 * Main API service for backend communication.
 * Similar to HttpClient services in Angular with error handling.
 */

import axios, { AxiosResponse, AxiosError } from 'axios';
import { ApiResponse, ApiError } from '@/types/api';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens (future enhancement)
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    const apiError: ApiError = {
      message: 'An unexpected error occurred',
      type: 'UnknownError',
      details: {}
    };

    if (error.response?.data) {
      const errorData = error.response.data as any;
      if (errorData.error) {
        apiError.message = errorData.error.message || errorData.error;
        apiError.type = errorData.error.type || 'ApiError';
        apiError.details = errorData.error.details || {};
      }
    } else if (error.request) {
      apiError.message = 'Network error - please check your connection';
      apiError.type = 'NetworkError';
    } else {
      apiError.message = error.message || 'Request configuration error';
      apiError.type = 'RequestError';
    }

    return Promise.reject(apiError);
  }
);

/**
 * Generic API response wrapper
 * Similar to Result<T> pattern in .NET
 */
export class ApiService {
  static async get<T>(url: string): Promise<ApiResponse<T>> {
    try {
      const response = await apiClient.get<T>(url);
      return {
        data: response.data,
        success: true
      };
    } catch (error) {
      return {
        error: error as ApiError,
        success: false
      };
    }
  }

  static async post<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response = await apiClient.post<T>(url, data);
      return {
        data: response.data,
        success: true
      };
    } catch (error) {
      return {
        error: error as ApiError,
        success: false
      };
    }
  }

  static async put<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response = await apiClient.put<T>(url, data);
      return {
        data: response.data,
        success: true
      };
    } catch (error) {
      return {
        error: error as ApiError,
        success: false
      };
    }
  }

  static async delete<T>(url: string): Promise<ApiResponse<T>> {
    try {
      const response = await apiClient.delete<T>(url);
      return {
        data: response.data,
        success: true
      };
    } catch (error) {
      return {
        error: error as ApiError,
        success: false
      };
    }
  }

  /**
   * Upload file with progress tracking
   * Similar to file upload services in .NET
   */
  static async uploadFile<T>(
    url: string, 
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<T>> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post<T>(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      });

      return {
        data: response.data,
        success: true
      };
    } catch (error) {
      return {
        error: error as ApiError,
        success: false
      };
    }
  }
}

export default ApiService;