import { apiClient } from './client';

export interface AdminCredentialsInput {
  first_name: string;
  last_name: string;
  email: string;
  username?: string;
  password: string;
  phone?: string;
}

export interface AcademicYearInput {
  name: string;
  start_date: string;
  end_date: string;
  is_current?: boolean;
}

export interface ClassTemplateItem {
  name: string;
  display_order: number;
  create_default_section?: boolean;
  default_section_name?: string;
  capacity?: number;
}

export interface SchoolOnboardingPayload {
  name: string;
  code: string;
  email?: string;
  phone?: string;
  website?: string;
  logo_url?: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  district: string;
  state: string;
  country?: string;
  postal_code: string;
  subscription_tier?: string;
  max_students?: number;
  max_teachers?: number;
  admin: AdminCredentialsInput;
  academic_year: AcademicYearInput;
  class_templates?: ClassTemplateItem[];
}

export interface SchoolOnboardingResult {
  school_id: string;
  name: string;
  code: string;
  status: string;
  subscription_tier: string;
  admin_user_id: string;
  admin_email: string;
  admin_name: string;
  academic_year_id: string;
  academic_year_name: string;
  roles_provisioned_count: number;
  classes_provisioned_count: number;
  message: string;
}

export const schoolOnboardingApi = {
  onboardSchool: async (payload: SchoolOnboardingPayload): Promise<SchoolOnboardingResult> => {
    const res = await apiClient.post('/schools/onboarding', payload);
    return res.data || res;
  },
};
