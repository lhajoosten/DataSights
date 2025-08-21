/**
 * API Service - Handles all communication with the backend
 * 
 * This service is the "communication layer" between our React frontend
 * and the Python FastAPI backend. It handles HTTP requests, responses,
 * error handling, and data formatting.
 * 
 * Key Responsibilities:
 * 1. Configure HTTP client with proper settings
 * 2. Handle authentication (future feature)
 * 3. Standardize error handling across all API calls
 * 4. Provide type-safe methods for different HTTP operations
 * 5. Transform responses into consistent format
 * 
 * This follows the "Service Layer" pattern - centralizing all API
 * communication logic in one place for maintainability.
 */

import axios, { AxiosResponse, AxiosError } from 'axios'; // HTTP client library
import { ApiResponse, ApiError } from '@/types/api';       // Our custom types

/**
 * Create configured axios instance
 * 
 * Axios is a popular HTTP client library. We create a pre-configured
 * instance with common settings that apply to all our API calls.
 */
const apiClient = axios.create({
  baseURL: '/api/v1',           // Base URL for all requests (backend API prefix)
  timeout: 30000,               // 30 second timeout (generous for AI processing)
  headers: {
    'Content-Type': 'application/json', // Default content type for requests
  },
});

/**
 * Request Interceptor - Runs before every request
 * 
 * Interceptors are middleware that can modify requests/responses.
 * This one adds authentication tokens to requests (future feature).
 * 
 * Why use interceptors?
 * - Centralized logic that applies to all requests
 * - No need to manually add auth headers to every API call
 * - Easy to modify auth logic in one place
 */
apiClient.interceptors.request.use(
  (config) => {
    // Check if we have an authentication token stored
    const token = localStorage.getItem('auth_token');
    if (token) {
      // Add Authorization header if token exists
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config; // Return modified config
  },
  (error) => Promise.reject(error) // Pass through errors
);

/**
 * Response Interceptor - Runs after every response
 * 
 * This interceptor standardizes error handling across all API calls.
 * Instead of handling errors differently in each component, we
 * transform all errors into a consistent format here.
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response, // Pass through successful responses
  (error: AxiosError) => {
    // Create standardized error object
    const apiError: ApiError = {
      message: 'An unexpected error occurred',
      type: 'UnknownError',
      details: {}
    };

    if (error.response?.data) {
      // Server responded with error data
      const errorData = error.response.data as any;
      if (errorData.error) {
        // Extract error details from backend response
        apiError.message = errorData.error.message || errorData.error;
        apiError.type = errorData.error.type || 'ApiError';
        apiError.details = errorData.error.details || {};
      }
    } else if (error.request) {
      // Network error (no response received)
      apiError.message = 'Network error - please check your connection';
      apiError.type = 'NetworkError';
    } else {
      // Request configuration error
      apiError.message = error.message || 'Request configuration error';
      apiError.type = 'RequestError';
    }

    // Reject with standardized error format
    return Promise.reject(apiError);
  }
);

/**
 * ApiService Class - Provides type-safe HTTP methods
 * 
 * This class wraps the axios client and provides standardized methods
 * for different types of HTTP requests. It follows the "Result Pattern"
 * where every response includes success/error indicators.
 * 
 * Benefits of this approach:
 * 1. Type Safety: TypeScript ensures we handle responses correctly
 * 2. Consistent Error Handling: All errors follow the same structure
 * 3. Explicit Success/Failure: Code must explicitly check for success
 * 4. Easy Testing: Mocking is straightforward with this interface
 */
export class ApiService {
  /**
   * HTTP GET request wrapper
   * 
   * Generic method for GET requests. The <T> syntax makes this a generic
   * function - it can work with any data type specified by the caller.
   * 
   * Example usage:
   * const result = await ApiService.get<UserData>('/users/123');
   * if (result.success) {
   *   console.log(result.data); // TypeScript knows this is UserData
   * }
   */
  static async get<T>(url: string): Promise<ApiResponse<T>> {
    try {
      // Make the HTTP GET request
      const response = await apiClient.get<T>(url);
      
      // Return success response
      return {
        data: response.data,
        success: true
      };
    } catch (error) {
      // Return error response (error was already formatted by interceptor)
      return {
        error: error as ApiError,
        success: false
      };
    }
  }

  /**
   * HTTP POST request wrapper
   * 
   * Generic method for POST requests (creating/sending data).
   */
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