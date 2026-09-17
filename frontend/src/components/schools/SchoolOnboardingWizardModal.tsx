import React, { useState } from 'react';
import {
  Building2,
  UserCheck,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  ChevronLeft,
  Loader2,
  Sparkles,
  ShieldAlert,
  Layers,
} from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  schoolOnboardingApi,
  SchoolOnboardingPayload,
  SchoolOnboardingResult,
  ClassTemplateItem,
} from '@/services/api/schoolOnboardingApi';

interface SchoolOnboardingWizardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const CLASS_PRESETS: Record<string, { label: string; description: string; classes: ClassTemplateItem[] }> = {
  K12: {
    label: 'K-12 Standard (Nursery to Class 12)',
    description: 'Pre-primary, Primary, Middle, Secondary, and Senior Secondary (14 classes with Section A).',
    classes: [
      { name: 'Nursery', display_order: 1, create_default_section: true, default_section_name: 'A', capacity: 30 },
      { name: 'LKG', display_order: 2, create_default_section: true, default_section_name: 'A', capacity: 30 },
      { name: 'UKG', display_order: 3, create_default_section: true, default_section_name: 'A', capacity: 30 },
      { name: 'Class 1', display_order: 4, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 2', display_order: 5, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 3', display_order: 6, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 4', display_order: 7, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 5', display_order: 8, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 6', display_order: 9, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 7', display_order: 10, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 8', display_order: 11, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 9', display_order: 12, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 10', display_order: 13, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 11', display_order: 14, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 12', display_order: 15, create_default_section: true, default_section_name: 'A', capacity: 40 },
    ],
  },
  PRIMARY: {
    label: 'Primary School (Class 1 to 5)',
    description: 'Elementary primary classes 1 through 5.',
    classes: [
      { name: 'Class 1', display_order: 1, create_default_section: true, default_section_name: 'A', capacity: 35 },
      { name: 'Class 2', display_order: 2, create_default_section: true, default_section_name: 'A', capacity: 35 },
      { name: 'Class 3', display_order: 3, create_default_section: true, default_section_name: 'A', capacity: 35 },
      { name: 'Class 4', display_order: 4, create_default_section: true, default_section_name: 'A', capacity: 35 },
      { name: 'Class 5', display_order: 5, create_default_section: true, default_section_name: 'A', capacity: 35 },
    ],
  },
  SECONDARY: {
    label: 'Secondary & Senior Secondary (Class 6 to 12)',
    description: 'Middle and high school grades 6 through 12.',
    classes: [
      { name: 'Class 6', display_order: 1, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 7', display_order: 2, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 8', display_order: 3, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 9', display_order: 4, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 10', display_order: 5, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 11', display_order: 6, create_default_section: true, default_section_name: 'A', capacity: 40 },
      { name: 'Class 12', display_order: 7, create_default_section: true, default_section_name: 'A', capacity: 40 },
    ],
  },
  NONE: {
    label: 'None / Blank Structure',
    description: 'Do not create initial classes; configure manually later.',
    classes: [],
  },
};

export const SchoolOnboardingWizardModal: React.FC<SchoolOnboardingWizardModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [provisionResult, setProvisionResult] = useState<SchoolOnboardingResult | null>(null);
  const [confirmed, setConfirmed] = useState<boolean>(false);

  // Form State
  const [schoolData, setSchoolData] = useState({
    name: '',
    code: '',
    email: '',
    phone: '',
    website: '',
    logo_url: '',
    address_line1: '',
    address_line2: '',
    city: '',
    district: '',
    state: '',
    country: 'India',
    postal_code: '',
    subscription_tier: 'STANDARD',
    max_students: 500,
    max_teachers: 50,
  });

  const [adminData, setAdminData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    username: '',
    password: '',
    confirm_password: '',
    phone: '',
  });

  const [academicData, setAcademicData] = useState({
    name: '2026-2027',
    start_date: '2026-06-01',
    end_date: '2027-04-30',
    preset: 'K12',
  });

  const resetState = () => {
    setCurrentStep(1);
    setIsSubmitting(false);
    setErrorMessage(null);
    setProvisionResult(null);
    setConfirmed(false);
    setSchoolData({
      name: '',
      code: '',
      email: '',
      phone: '',
      website: '',
      logo_url: '',
      address_line1: '',
      address_line2: '',
      city: '',
      district: '',
      state: '',
      country: 'India',
      postal_code: '',
      subscription_tier: 'STANDARD',
      max_students: 500,
      max_teachers: 50,
    });
    setAdminData({
      first_name: '',
      last_name: '',
      email: '',
      username: '',
      password: '',
      confirm_password: '',
      phone: '',
    });
    setAcademicData({
      name: '2026-2027',
      start_date: '2026-06-01',
      end_date: '2027-04-30',
      preset: 'K12',
    });
  };

  const handleClose = () => {
    if (!isSubmitting) {
      resetState();
      onClose();
    }
  };

  // Validation
  const validateStep1 = (): boolean => {
    if (!schoolData.name.trim() || schoolData.name.length < 2) {
      setErrorMessage('Please provide a valid school name (min 2 characters).');
      return false;
    }
    if (!schoolData.code.trim() || schoolData.code.length < 2) {
      setErrorMessage('Please provide a unique school code (e.g. GWH, DPS01).');
      return false;
    }
    if (!schoolData.address_line1.trim() || !schoolData.city.trim() || !schoolData.district.trim() || !schoolData.state.trim() || !schoolData.postal_code.trim()) {
      setErrorMessage('Please fill in all mandatory address fields.');
      return false;
    }
    setErrorMessage(null);
    return true;
  };

  const validateStep2 = (): boolean => {
    if (!adminData.first_name.trim() || !adminData.last_name.trim()) {
      setErrorMessage('Please enter the administrator first and last name.');
      return false;
    }
    if (!adminData.email.trim() || !adminData.email.includes('@')) {
      setErrorMessage('Please provide a valid administrator email address.');
      return false;
    }
    if (adminData.password.length < 8) {
      setErrorMessage('Administrator password must be at least 8 characters long.');
      return false;
    }
    if (adminData.password !== adminData.confirm_password) {
      setErrorMessage('Password and Confirm Password do not match.');
      return false;
    }
    setErrorMessage(null);
    return true;
  };

  const validateStep3 = (): boolean => {
    if (!academicData.name.trim()) {
      setErrorMessage('Please provide an academic year name (e.g. 2026-2027).');
      return false;
    }
    if (!academicData.start_date || !academicData.end_date) {
      setErrorMessage('Please provide both start and end dates.');
      return false;
    }
    if (new Date(academicData.start_date) >= new Date(academicData.end_date)) {
      setErrorMessage('Academic year start date must be before the end date.');
      return false;
    }
    setErrorMessage(null);
    return true;
  };

  const handleNext = () => {
    if (currentStep === 1 && validateStep1()) {
      setCurrentStep(2);
    } else if (currentStep === 2 && validateStep2()) {
      setCurrentStep(3);
    } else if (currentStep === 3 && validateStep3()) {
      setCurrentStep(4);
    }
  };

  const handleBack = () => {
    setErrorMessage(null);
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleProvisionSubmit = async () => {
    if (!confirmed) {
      setErrorMessage('Please confirm authorization by checking the confirmation box.');
      return;
    }

    setErrorMessage(null);
    setIsSubmitting(true);

    const payload: SchoolOnboardingPayload = {
      name: schoolData.name.trim(),
      code: schoolData.code.trim().toUpperCase(),
      email: schoolData.email.trim() || undefined,
      phone: schoolData.phone.trim() || undefined,
      website: schoolData.website.trim() || undefined,
      logo_url: schoolData.logo_url.trim() || undefined,
      address_line1: schoolData.address_line1.trim(),
      address_line2: schoolData.address_line2.trim() || undefined,
      city: schoolData.city.trim(),
      district: schoolData.district.trim(),
      state: schoolData.state.trim(),
      country: schoolData.country.trim() || 'India',
      postal_code: schoolData.postal_code.trim(),
      subscription_tier: schoolData.subscription_tier,
      max_students: Number(schoolData.max_students) || undefined,
      max_teachers: Number(schoolData.max_teachers) || undefined,
      admin: {
        first_name: adminData.first_name.trim(),
        last_name: adminData.last_name.trim(),
        email: adminData.email.trim(),
        username: adminData.username.trim() || undefined,
        password: adminData.password,
        phone: adminData.phone.trim() || undefined,
      },
      academic_year: {
        name: academicData.name.trim(),
        start_date: academicData.start_date,
        end_date: academicData.end_date,
        is_current: true,
      },
      class_templates: CLASS_PRESETS[academicData.preset]?.classes || [],
    };

    try {
      const result = await schoolOnboardingApi.onboardSchool(payload);
      setProvisionResult(result);
      onSuccess();
    } catch (err: any) {
      const msg = err.response?.data?.message || err.message || 'Failed to provision school tenant. Please check constraints.';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="School Tenant Onboarding & Provisioning Wizard"
      size="xl"
    >
      <div className="space-y-6">
        {/* Step Progress Bar */}
        <div className="flex items-center justify-between border-b pb-4">
          <div className={`flex items-center space-x-2 ${currentStep >= 1 ? 'text-indigo-600 font-semibold' : 'text-gray-400'}`}>
            <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${currentStep >= 1 ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-700'}`}>
              1
            </span>
            <span className="text-sm hidden sm:inline">School Identity</span>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-300" />
          <div className={`flex items-center space-x-2 ${currentStep >= 2 ? 'text-indigo-600 font-semibold' : 'text-gray-400'}`}>
            <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${currentStep >= 2 ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-700'}`}>
              2
            </span>
            <span className="text-sm hidden sm:inline">Admin User</span>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-300" />
          <div className={`flex items-center space-x-2 ${currentStep >= 3 ? 'text-indigo-600 font-semibold' : 'text-gray-400'}`}>
            <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${currentStep >= 3 ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-700'}`}>
              3
            </span>
            <span className="text-sm hidden sm:inline">Academic Setup</span>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-300" />
          <div className={`flex items-center space-x-2 ${currentStep >= 4 ? 'text-indigo-600 font-semibold' : 'text-gray-400'}`}>
            <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${currentStep >= 4 ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-700'}`}>
              4
            </span>
            <span className="text-sm hidden sm:inline">Provision</span>
          </div>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2 text-sm text-red-700">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 text-red-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Success View */}
        {provisionResult ? (
          <div className="py-6 text-center space-y-4">
            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-10 h-10" />
            </div>
            <h3 className="text-xl font-bold text-gray-900">Tenant Provisioned Successfully!</h3>
            <p className="text-sm text-gray-600 max-w-md mx-auto">
              School <strong className="text-gray-900">{provisionResult.name}</strong> ({provisionResult.code}) is now active with all default roles, permissions, and academic configurations.
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-gray-50 p-4 rounded-xl text-left border">
              <div>
                <p className="text-xs text-gray-500">School Code</p>
                <p className="text-sm font-semibold text-gray-900">{provisionResult.code}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Initial Admin</p>
                <p className="text-sm font-semibold text-gray-900 truncate">{provisionResult.admin_email}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Roles Seeded</p>
                <p className="text-sm font-semibold text-gray-900">{provisionResult.roles_provisioned_count} System Roles</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Classes</p>
                <p className="text-sm font-semibold text-gray-900">{provisionResult.classes_provisioned_count} Classes</p>
              </div>
            </div>

            <div className="pt-4">
              <Button variant="primary" onClick={handleClose}>
                Done & Close
              </Button>
            </div>
          </div>
        ) : (
          <>
            {/* Step 1: School Identity */}
            {currentStep === 1 && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-gray-700 pb-2 border-b">
                  <Building2 className="w-5 h-5 text-indigo-600" />
                  <span className="font-semibold text-sm">School Details & Address</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      School Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      aria-label="School Name"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. Greenwood International High School"
                      value={schoolData.name}
                      onChange={(e) => setSchoolData({ ...schoolData, name: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      School Code (Unique ID) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      aria-label="School Code"
                      className="w-full px-3 py-2 border rounded-lg text-sm uppercase focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. GWH01"
                      value={schoolData.code}
                      onChange={(e) => setSchoolData({ ...schoolData, code: e.target.value.toUpperCase() })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Official Email</label>
                    <input
                      type="email"
                      aria-label="Official Email"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. info@greenwood.edu"
                      value={schoolData.email}
                      onChange={(e) => setSchoolData({ ...schoolData, email: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Contact Phone</label>
                    <input
                      type="text"
                      aria-label="Contact Phone"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. +91 9876543210"
                      value={schoolData.phone}
                      onChange={(e) => setSchoolData({ ...schoolData, phone: e.target.value })}
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Address Line 1 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      aria-label="Address Line 1"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="Street address, campus building"
                      value={schoolData.address_line1}
                      onChange={(e) => setSchoolData({ ...schoolData, address_line1: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      City <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      aria-label="City"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. Bangalore"
                      value={schoolData.city}
                      onChange={(e) => setSchoolData({ ...schoolData, city: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      District <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      aria-label="District"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. Bangalore Urban"
                      value={schoolData.district}
                      onChange={(e) => setSchoolData({ ...schoolData, district: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      State <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      aria-label="State"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. Karnataka"
                      value={schoolData.state}
                      onChange={(e) => setSchoolData({ ...schoolData, state: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Postal Code (PIN) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      aria-label="Postal Code"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. 560001"
                      value={schoolData.postal_code}
                      onChange={(e) => setSchoolData({ ...schoolData, postal_code: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Subscription Tier</label>
                    <select
                      aria-label="Subscription Tier"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={schoolData.subscription_tier}
                      onChange={(e) => setSchoolData({ ...schoolData, subscription_tier: e.target.value })}
                    >
                      <option value="STANDARD">STANDARD</option>
                      <option value="PREMIUM">PREMIUM</option>
                      <option value="ENTERPRISE">ENTERPRISE</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Max Student Capacity</label>
                    <input
                      type="number"
                      aria-label="Max Student Capacity"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={schoolData.max_students}
                      onChange={(e) => setSchoolData({ ...schoolData, max_students: parseInt(e.target.value) || 0 })}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Administrator */}
            {currentStep === 2 && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-gray-700 pb-2 border-b">
                  <UserCheck className="w-5 h-5 text-indigo-600" />
                  <span className="font-semibold text-sm">Initial School Administrator Account</span>
                </div>

                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800">
                  This user will be provisioned as the tenant's primary <strong>School Admin</strong> with full operational and academic access.
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      First Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      aria-label="Admin First Name"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. Sarah"
                      value={adminData.first_name}
                      onChange={(e) => setAdminData({ ...adminData, first_name: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Last Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      aria-label="Admin Last Name"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. Jenkins"
                      value={adminData.last_name}
                      onChange={(e) => setAdminData({ ...adminData, last_name: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Admin Email <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="email"
                      aria-label="Admin Email"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. admin@school.edu"
                      value={adminData.email}
                      onChange={(e) => setAdminData({ ...adminData, email: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Username (Optional)</label>
                    <input
                      type="text"
                      aria-label="Admin Username"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. sjenkins_admin"
                      value={adminData.username}
                      onChange={(e) => setAdminData({ ...adminData, username: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Password (Min 8 chars) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="password"
                      aria-label="Admin Password"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="••••••••••••"
                      value={adminData.password}
                      onChange={(e) => setAdminData({ ...adminData, password: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Confirm Password <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="password"
                      aria-label="Confirm Password"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="••••••••••••"
                      value={adminData.confirm_password}
                      onChange={(e) => setAdminData({ ...adminData, confirm_password: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">Phone Number</label>
                    <input
                      type="text"
                      aria-label="Admin Phone"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. +91 9876543211"
                      value={adminData.phone}
                      onChange={(e) => setAdminData({ ...adminData, phone: e.target.value })}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Academic Setup & Classes */}
            {currentStep === 3 && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-gray-700 pb-2 border-b">
                  <Calendar className="w-5 h-5 text-indigo-600" />
                  <span className="font-semibold text-sm">Academic Calendar & Initial Class Templates</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Academic Year Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      aria-label="Academic Year Name"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. 2026-2027"
                      value={academicData.name}
                      onChange={(e) => setAcademicData({ ...academicData, name: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Start Date <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      aria-label="Academic Start Date"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={academicData.start_date}
                      onChange={(e) => setAcademicData({ ...academicData, start_date: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      End Date <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      aria-label="Academic End Date"
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={academicData.end_date}
                      onChange={(e) => setAcademicData({ ...academicData, end_date: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-3 pt-2">
                  <label className="block text-xs font-semibold text-gray-700">Initial Class Structure Preset</label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {Object.entries(CLASS_PRESETS).map(([key, item]) => {
                      const isSelected = academicData.preset === key;
                      return (
                        <div
                          key={key}
                          onClick={() => setAcademicData({ ...academicData, preset: key })}
                          className={`p-3 rounded-xl border cursor-pointer transition-all ${
                            isSelected
                              ? 'border-indigo-600 bg-indigo-50/50 shadow-sm ring-1 ring-indigo-600'
                              : 'border-gray-200 hover:border-gray-300 bg-white'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-bold text-gray-900">{item.label}</h4>
                            <Badge variant={isSelected ? 'success' : 'neutral'} size="sm">
                              {item.classes.length} Classes
                            </Badge>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">{item.description}</p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* Step 4: Review & Provision */}
            {currentStep === 4 && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-gray-700 pb-2 border-b">
                  <Sparkles className="w-5 h-5 text-indigo-600" />
                  <span className="font-semibold text-sm">Review & Provision Tenant</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                  {/* School Summary */}
                  <div className="p-3 bg-gray-50 rounded-xl border space-y-1.5">
                    <p className="font-bold text-gray-900 border-b pb-1">School Entity</p>
                    <p className="text-gray-700"><strong>Name:</strong> {schoolData.name}</p>
                    <p className="text-gray-700"><strong>Code:</strong> {schoolData.code}</p>
                    <p className="text-gray-700"><strong>City:</strong> {schoolData.city}, {schoolData.state}</p>
                    <p className="text-gray-700"><strong>Tier:</strong> {schoolData.subscription_tier}</p>
                  </div>

                  {/* Admin Summary */}
                  <div className="p-3 bg-gray-50 rounded-xl border space-y-1.5">
                    <p className="font-bold text-gray-900 border-b pb-1">Administrator</p>
                    <p className="text-gray-700"><strong>Name:</strong> {adminData.first_name} {adminData.last_name}</p>
                    <p className="text-gray-700 truncate"><strong>Email:</strong> {adminData.email}</p>
                    <p className="text-gray-700"><strong>Role:</strong> School Admin</p>
                    <p className="text-gray-700"><strong>Password:</strong> •••••••• (Argon2id)</p>
                  </div>

                  {/* Academic Summary */}
                  <div className="p-3 bg-gray-50 rounded-xl border space-y-1.5">
                    <p className="font-bold text-gray-900 border-b pb-1">Academic & Classes</p>
                    <p className="text-gray-700"><strong>Year:</strong> {academicData.name}</p>
                    <p className="text-gray-700"><strong>Dates:</strong> {academicData.start_date} to {academicData.end_date}</p>
                    <p className="text-gray-700"><strong>Structure:</strong> {CLASS_PRESETS[academicData.preset]?.label}</p>
                    <p className="text-gray-700"><strong>Roles Seeded:</strong> 12 System Roles</p>
                  </div>
                </div>

                {/* Atomic Transaction Banner */}
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start space-x-2 text-xs text-amber-800">
                  <ShieldAlert className="w-4 h-4 flex-shrink-0 text-amber-600 mt-0.5" />
                  <div>
                    <p className="font-semibold">Atomic Provisioning Guarantee</p>
                    <p className="text-amber-700">
                      This action will create the tenant school, seed all system roles & permission links, provision the initial administrator, establish the primary academic year, and create initial classes in a single fail-closed database transaction.
                    </p>
                  </div>
                </div>

                {/* Confirmation Checkbox */}
                <div className="flex items-center space-x-2 pt-2">
                  <input
                    type="checkbox"
                    id="provision-confirm-checkbox"
                    aria-label="Confirm Provisioning"
                    checked={confirmed}
                    onChange={(e) => setConfirmed(e.target.checked)}
                    className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500 border-gray-300"
                  />
                  <label htmlFor="provision-confirm-checkbox" className="text-xs font-semibold text-gray-700 cursor-pointer">
                    I confirm all details are accurate and authorize platform tenant provisioning.
                  </label>
                </div>
              </div>
            )}

            {/* Wizard Navigation Footer */}
            <div className="flex items-center justify-between border-t pt-4">
              <Button
                variant="outline"
                onClick={currentStep === 1 ? handleClose : handleBack}
                disabled={isSubmitting}
              >
                {currentStep === 1 ? 'Cancel' : 'Back'}
              </Button>

              {currentStep < 4 ? (
                <Button variant="primary" onClick={handleNext}>
                  <span>Next Step</span>
                  <ChevronRight className="w-4 h-4 ml-1 inline" />
                </Button>
              ) : (
                <Button
                  variant="primary"
                  onClick={handleProvisionSubmit}
                  disabled={!confirmed || isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin inline" />
                      <span>Provisioning Tenant...</span>
                    </>
                  ) : (
                    <span>Provision School Tenant</span>
                  )}
                </Button>
              )}
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};
