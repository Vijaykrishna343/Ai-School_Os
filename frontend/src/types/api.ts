export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data: T | null;
  errors: Record<string, string> | null;
}

export interface ApiError {
  message: string;
  status?: number;
  errors?: Record<string, string> | null;
}
