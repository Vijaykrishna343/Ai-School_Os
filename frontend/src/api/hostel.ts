import { apiClient } from '@/services/api/client';

export interface HostelDashboardMetrics {
  total_hostels: number;
  total_rooms: number;
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  occupancy_percentage: number;
  today_present_count: number;
  pending_outpasses: number;
  checked_out_students: number;
}

export interface HostelBuilding {
  id: string;
  name: string;
  code: string;
  gender_designation: string;
  capacity: number;
  is_active: boolean;
  description?: string;
}

export interface HostelRoom {
  id: string;
  building_id: string;
  room_number: string;
  floor: number;
  room_type: string;
  capacity: number;
  is_active: boolean;
  notes?: string;
}

export interface HostelBed {
  id: string;
  room_id: string;
  bed_number: string;
  status: string;
  is_active: boolean;
}

export interface HostelOutpass {
  id: string;
  student_id: string;
  building_id: string;
  room_id: string;
  reason: string;
  destination: string;
  departure_time: string;
  expected_return_time: string;
  actual_checkout_time?: string;
  actual_return_time?: string;
  status: string;
  remarks?: string;
}

export interface HostelFeeStructure {
  id: string;
  academic_year_id: string;
  name: string;
  amount: number;
  description?: string;
}

export const hostelApi = {
  getDashboard: async (): Promise<HostelDashboardMetrics> => {
    const res = await apiClient.get('/api/v1/hostel/dashboard');
    return res.data.data;
  },

  getBuildings: async (): Promise<HostelBuilding[]> => {
    const res = await apiClient.get('/api/v1/hostel/buildings');
    return res.data.data;
  },

  createBuilding: async (data: Partial<HostelBuilding>): Promise<any> => {
    const res = await apiClient.post('/api/v1/hostel/buildings', data);
    return res.data;
  },

  getRooms: async (buildingId?: string): Promise<HostelRoom[]> => {
    const res = await apiClient.get('/api/v1/hostel/rooms', { params: { building_id: buildingId } });
    return res.data.data;
  },

  createRoom: async (buildingId: string, data: Partial<HostelRoom>): Promise<any> => {
    const res = await apiClient.post(`/api/v1/hostel/buildings/${buildingId}/rooms`, data);
    return res.data;
  },

  getBeds: async (roomId?: string): Promise<HostelBed[]> => {
    const res = await apiClient.get('/api/v1/hostel/beds', { params: { room_id: roomId } });
    return res.data.data;
  },

  createBed: async (roomId: string, data: Partial<HostelBed>): Promise<any> => {
    const res = await apiClient.post(`/api/v1/hostel/rooms/${roomId}/beds`, data);
    return res.data;
  },

  getOutpasses: async (studentId?: string, status?: string): Promise<HostelOutpass[]> => {
    const res = await apiClient.get('/api/v1/hostel/outpasses', { params: { student_id: studentId, status } });
    return res.data.data;
  },

  createOutpass: async (data: any): Promise<any> => {
    const res = await apiClient.post('/api/v1/hostel/outpasses', data);
    return res.data;
  },

  approveOutpass: async (outpassId: string, approve: boolean, remarks?: string): Promise<any> => {
    const res = await apiClient.put(`/api/v1/hostel/outpasses/${outpassId}/approve`, { approve, remarks });
    return res.data;
  },

  getFeeStructures: async (academicYearId?: string): Promise<HostelFeeStructure[]> => {
    const res = await apiClient.get('/api/v1/hostel/fees/structures', { params: { academic_year_id: academicYearId } });
    return res.data.data;
  },

  createFeeStructure: async (data: any): Promise<any> => {
    const res = await apiClient.post('/api/v1/hostel/fees/structures', data);
    return res.data;
  },
};
