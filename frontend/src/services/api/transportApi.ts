import { apiClient } from './client';
import {
  PaginatedResponse,
  RouteStop,
  RouteStopCreate,
  RouteStopUpdate,
  StudentTransportAllocation,
  StudentTransportAllocationCreate,
  StudentTransportAllocationStatusUpdate,
  StudentTransportAllocationUpdate,
  TransportDashboardStats,
  TransportDriver,
  TransportDriverCreate,
  TransportDriverUpdate,
  TransportRoute,
  TransportRouteCreate,
  TransportRouteUpdate,
  TransportVehicle,
  TransportVehicleCreate,
  TransportVehicleUpdate,
} from '@/types/models';

export interface VehicleFilterParams {
  status?: string;
  vehicle_type?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface DriverFilterParams {
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface RouteFilterParams {
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface AllocationFilterParams {
  route_id?: string;
  academic_year_id?: string;
  status?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const transportApi = {
  // Dashboard Operations
  getDashboardStats: async (): Promise<TransportDashboardStats> => {
    return await apiClient.get('/transport/dashboard-stats');
  },

  // Vehicle Operations
  getVehicles: async (params?: VehicleFilterParams): Promise<PaginatedResponse<TransportVehicle>> => {
    return await apiClient.get('/transport/vehicles', { params });
  },

  getVehicle: async (id: string): Promise<TransportVehicle> => {
    return await apiClient.get(`/transport/vehicles/${id}`);
  },

  createVehicle: async (data: TransportVehicleCreate): Promise<TransportVehicle> => {
    return await apiClient.post('/transport/vehicles', data);
  },

  updateVehicle: async (id: string, data: TransportVehicleUpdate): Promise<TransportVehicle> => {
    return await apiClient.patch(`/transport/vehicles/${id}`, data);
  },

  deleteVehicle: async (id: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.delete(`/transport/vehicles/${id}`);
  },

  // Driver Operations
  getDrivers: async (params?: DriverFilterParams): Promise<PaginatedResponse<TransportDriver>> => {
    return await apiClient.get('/transport/drivers', { params });
  },

  getDriver: async (id: string): Promise<TransportDriver> => {
    return await apiClient.get(`/transport/drivers/${id}`);
  },

  createDriver: async (data: TransportDriverCreate): Promise<TransportDriver> => {
    return await apiClient.post('/transport/drivers', data);
  },

  updateDriver: async (id: string, data: TransportDriverUpdate): Promise<TransportDriver> => {
    return await apiClient.patch(`/transport/drivers/${id}`, data);
  },

  deleteDriver: async (id: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.delete(`/transport/drivers/${id}`);
  },

  // Route Operations
  getRoutes: async (params?: RouteFilterParams): Promise<PaginatedResponse<TransportRoute>> => {
    return await apiClient.get('/transport/routes', { params });
  },

  getRoute: async (id: string): Promise<TransportRoute> => {
    return await apiClient.get(`/transport/routes/${id}`);
  },

  createRoute: async (data: TransportRouteCreate): Promise<TransportRoute> => {
    return await apiClient.post('/transport/routes', data);
  },

  updateRoute: async (id: string, data: TransportRouteUpdate): Promise<TransportRoute> => {
    return await apiClient.patch(`/transport/routes/${id}`, data);
  },

  deleteRoute: async (id: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.delete(`/transport/routes/${id}`);
  },

  // Route Stop Operations
  getStops: async (routeId: string): Promise<RouteStop[]> => {
    return await apiClient.get(`/transport/routes/${routeId}/stops`);
  },

  getStop: async (routeId: string, stopId: string): Promise<RouteStop> => {
    return await apiClient.get(`/transport/routes/${routeId}/stops/${stopId}`);
  },

  createStop: async (routeId: string, data: RouteStopCreate): Promise<RouteStop> => {
    return await apiClient.post(`/transport/routes/${routeId}/stops`, data);
  },

  updateStop: async (routeId: string, stopId: string, data: RouteStopUpdate): Promise<RouteStop> => {
    return await apiClient.patch(`/transport/routes/${routeId}/stops/${stopId}`, data);
  },

  deleteStop: async (routeId: string, stopId: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.delete(`/transport/routes/${routeId}/stops/${stopId}`);
  },

  // Allocation Operations
  getAllocations: async (params?: AllocationFilterParams): Promise<PaginatedResponse<StudentTransportAllocation>> => {
    return await apiClient.get('/transport/allocations', { params });
  },

  getAllocation: async (id: string): Promise<StudentTransportAllocation> => {
    return await apiClient.get(`/transport/allocations/${id}`);
  },

  createAllocation: async (data: StudentTransportAllocationCreate): Promise<StudentTransportAllocation> => {
    return await apiClient.post('/transport/allocations', data);
  },

  updateAllocation: async (id: string, data: StudentTransportAllocationUpdate): Promise<StudentTransportAllocation> => {
    return await apiClient.patch(`/transport/allocations/${id}`, data);
  },

  updateAllocationStatus: async (
    id: string,
    data: StudentTransportAllocationStatusUpdate
  ): Promise<StudentTransportAllocation> => {
    return await apiClient.patch(`/transport/allocations/${id}/status`, data);
  },

  deleteAllocation: async (id: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.delete(`/transport/allocations/${id}`);
  },
};
