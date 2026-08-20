export interface User {
  id: string;
  school_id: string;
  email: string;
  username?: string | null;
  first_name: string;
  last_name?: string | null;
  phone?: string | null;
  is_active: boolean;
  status?: string;
  is_super_admin?: boolean;
  is_verified?: boolean;
  last_login?: string | null;
}


export interface UserRole {
  id: string;
  name: string;
  code: string;
  permissions?: RolePermission[];
}

export interface RolePermission {
  id: string;
  name: string;
  module: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserLoginPayload {
  school_code: string;
  email: string;
  password: string;
}
