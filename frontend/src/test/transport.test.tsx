import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TransportPage } from '@/pages/TransportPage';
import { transportApi } from '@/services/api/transportApi';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { studentsApi } from '@/services/api/studentsApi';
import { teachersApi } from '@/services/api/teachersApi';
import { useAuthStore } from '@/store/useAuthStore';
import {
  TransportDashboardStats,
  TransportVehicle,
  TransportDriver,
  TransportRoute,
  RouteStop,
  StudentTransportAllocation,
  PaginatedResponse,
} from '@/types/models';

// Mock transportApi
vi.mock('@/services/api/transportApi', () => ({
  transportApi: {
    getDashboardStats: vi.fn(),
    getVehicles: vi.fn(),
    getVehicle: vi.fn(),
    createVehicle: vi.fn(),
    updateVehicle: vi.fn(),
    deleteVehicle: vi.fn(),
    getDrivers: vi.fn(),
    getDriver: vi.fn(),
    createDriver: vi.fn(),
    updateDriver: vi.fn(),
    deleteDriver: vi.fn(),
    getRoutes: vi.fn(),
    getRoute: vi.fn(),
    createRoute: vi.fn(),
    updateRoute: vi.fn(),
    deleteRoute: vi.fn(),
    getStops: vi.fn(),
    getStop: vi.fn(),
    createStop: vi.fn(),
    updateStop: vi.fn(),
    deleteStop: vi.fn(),
    getAllocations: vi.fn(),
    getAllocation: vi.fn(),
    createAllocation: vi.fn(),
    updateAllocation: vi.fn(),
    updateAllocationStatus: vi.fn(),
    deleteAllocation: vi.fn(),
  },
}));

// Mock academicYearsApi
vi.mock('@/services/api/academicYearsApi', () => ({
  academicYearsApi: {
    getAcademicYears: vi.fn().mockResolvedValue([
      { id: 'ay-1', name: '2026-2027', status: 'ACTIVE', is_current: true },
    ]),
  },
}));

// Mock studentsApi
vi.mock('@/services/api/studentsApi', () => ({
  studentsApi: {
    getStudents: vi.fn().mockResolvedValue({
      items: [
        { id: 'stud-1', first_name: 'Aarav', last_name: 'Sharma', admission_number: 'ADM-101' },
        { id: 'stud-2', first_name: 'Diya', last_name: 'Patel', admission_number: 'ADM-102' },
      ],
      total: 2,
    }),
  },
}));

// Mock teachersApi
vi.mock('@/services/api/teachersApi', () => ({
  teachersApi: {
    getTeachers: vi.fn().mockResolvedValue({
      items: [
        { id: 't-1', first_name: 'Rajesh', last_name: 'Verma', employee_id: 'EMP-001' },
      ],
      total: 1,
    }),
  },
}));

// Mock data fixtures
const mockDashboardStats: TransportDashboardStats = {
  total_vehicles: 5,
  active_vehicles: 4,
  maintenance_vehicles: 1,
  decommissioned_vehicles: 0,
  total_drivers: 4,
  active_drivers: 4,
  total_routes: 3,
  active_routes: 3,
  total_stops: 12,
  active_allocations: 45,
  total_seating_capacity: 150,
  total_occupied_seats: 45,
  total_available_seats: 105,
  overall_occupancy_rate_percent: 30.0,
  vehicles_occupancy: [
    {
      vehicle_id: 'veh-1',
      registration_number: 'TS09AB1001',
      vehicle_code: 'BUS-01',
      seating_capacity: 50,
      total_allocated_seats: 25,
      available_seats: 25,
      occupancy_rate_percent: 50.0,
      routes_count: 1,
    },
  ],
};

const mockVehiclesList: PaginatedResponse<TransportVehicle> = {
  items: [
    {
      id: 'veh-1',
      school_id: 'sch-1',
      registration_number: 'TS09AB1001',
      vehicle_code: 'BUS-01',
      vehicle_type: 'BUS',
      seating_capacity: 50,
      fuel_type: 'DIESEL',
      insurance_expiry_date: '2027-01-01',
      fitness_expiry_date: '2027-01-01',
      status: 'ACTIVE',
      created_at: '2026-06-01T00:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

const mockDriversList: PaginatedResponse<TransportDriver> = {
  items: [
    {
      id: 'drv-1',
      school_id: 'sch-1',
      driver_name: 'Suresh Rao',
      license_number: 'DL-0420110099',
      license_expiry_date: '2028-05-15',
      contact_phone: '9876543210',
      emergency_contact: '9876500000',
      is_active: true,
      created_at: '2026-06-01T00:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

const mockRoutesList: PaginatedResponse<TransportRoute> = {
  items: [
    {
      id: 'rt-1',
      school_id: 'sch-1',
      route_code: 'R-NORTH-1',
      route_name: 'North Campus Express',
      vehicle_id: 'veh-1',
      driver_id: 'drv-1',
      morning_start_time: '07:30',
      evening_start_time: '15:30',
      is_active: true,
      created_at: '2026-06-01T00:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

const mockStopsList: RouteStop[] = [
  {
    id: 'stp-1',
    school_id: 'sch-1',
    route_id: 'rt-1',
    stop_name: 'Jubilee Hills Checkpost',
    stop_code: 'JH-01',
    sequence_order: 1,
    morning_pickup_time: '07:45',
    afternoon_drop_time: '16:00',
    pickup_fee_amount: '600.00',
    is_active: true,
    created_at: '2026-06-01T00:00:00Z',
  },
  {
    id: 'stp-2',
    school_id: 'sch-1',
    route_id: 'rt-1',
    stop_name: 'Madhapur Metro',
    stop_code: 'MD-02',
    sequence_order: 2,
    morning_pickup_time: '08:00',
    afternoon_drop_time: '15:45',
    pickup_fee_amount: '600.00',
    is_active: true,
    created_at: '2026-06-01T00:00:00Z',
  },
];

const mockAllocationsList: PaginatedResponse<StudentTransportAllocation> = {
  items: [
    {
      id: 'alloc-1',
      school_id: 'sch-1',
      student_id: 'stud-1',
      student_name: 'Aarav Sharma',
      admission_number: 'ADM-101',
      route_id: 'rt-1',
      route_code: 'R-NORTH-1',
      pickup_stop_id: 'stp-1',
      pickup_stop_name: 'Jubilee Hills Checkpost',
      drop_stop_id: 'stp-2',
      drop_stop_name: 'Madhapur Metro',
      academic_year_id: 'ay-1',
      allocation_type: 'TWO_WAY',
      status: 'ACTIVE',
      start_date: '2026-06-01',
      created_at: '2026-06-01T00:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

describe('TransportPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default Super Admin auth state
    useAuthStore.setState({
      user: { id: 'usr-1', email: 'admin@school.com', is_super_admin: true } as any,
      permissions: [
        'transport.view',
        'transport.create',
        'transport.update',
        'transport.delete',
        'transport.allocate',
        'transport.manage',
      ],
      roles: [{ id: 'r1', name: 'SUPER_ADMIN', code: 'SUPER_ADMIN' }],
      isAuthenticated: true,
    });

    vi.mocked(transportApi.getDashboardStats).mockResolvedValue(mockDashboardStats);
    vi.mocked(transportApi.getVehicles).mockResolvedValue(mockVehiclesList);
    vi.mocked(transportApi.getDrivers).mockResolvedValue(mockDriversList);
    vi.mocked(transportApi.getRoutes).mockResolvedValue(mockRoutesList);
    vi.mocked(transportApi.getStops).mockResolvedValue(mockStopsList);
    vi.mocked(transportApi.getAllocations).mockResolvedValue(mockAllocationsList);
  });

  it('1. Renders Transport Management header and KPI summary cards on Overview tab', async () => {
    render(<TransportPage />);

    expect(await screen.findByText('Transport Fleet & Logistics')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Dashboard Overview/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Fleet Management/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Drivers Directory/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Transit Routes & Stops/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Student Allocations/i })).toBeInTheDocument();

    // Verify KPI stats render
    expect(await screen.findByText('Fleet Vehicles')).toBeInTheDocument();
    expect(screen.getByText('Active Drivers')).toBeInTheDocument();
    expect(screen.getByText('Transit Routes')).toBeInTheDocument();
    expect(screen.getByText('Fleet Seating & Capacity Distribution')).toBeInTheDocument();
  });

  it('2. Switches to Fleet Management tab and renders vehicle list', async () => {
    render(<TransportPage />);

    const fleetTab = await screen.findByText('Fleet Management');
    fireEvent.click(fleetTab);

    expect(await screen.findByText('BUS-01')).toBeInTheDocument();
    expect(screen.getByText('TS09AB1001')).toBeInTheDocument();
    expect(screen.getByText('50 seats')).toBeInTheDocument();
    expect(screen.getByText('Add Vehicle')).toBeInTheDocument();
  });

  it('3. Opens Add Vehicle modal, fills form, and submits creation payload', async () => {
    vi.mocked(transportApi.createVehicle).mockResolvedValue({
      id: 'veh-new',
      school_id: 'sch-1',
      registration_number: 'TS09XY9999',
      vehicle_code: 'BUS-02',
      vehicle_type: 'BUS',
      seating_capacity: 40,
      fuel_type: 'DIESEL',
      status: 'ACTIVE',
      created_at: '2026-06-01T00:00:00Z',
    });

    render(<TransportPage />);

    const fleetTab = await screen.findByText('Fleet Management');
    fireEvent.click(fleetTab);

    const addBtn = await screen.findByText('Add Vehicle');
    fireEvent.click(addBtn);

    expect(screen.getByText('Add New Fleet Vehicle')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText('e.g. TS09AB1234'), {
      target: { value: 'TS09XY9999' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g. BUS-01'), {
      target: { value: 'BUS-02' },
    });

    const submitBtn = screen.getByText('Create Vehicle');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(transportApi.createVehicle).toHaveBeenCalledWith(
        expect.objectContaining({
          registration_number: 'TS09XY9999',
          vehicle_code: 'BUS-02',
          seating_capacity: 30,
        })
      );
    });
  });

  it('4. Switches to Drivers tab and renders driver list', async () => {
    render(<TransportPage />);

    const driversTab = await screen.findByText('Drivers Directory');
    fireEvent.click(driversTab);

    expect(await screen.findByText('Suresh Rao')).toBeInTheDocument();
    expect(screen.getByText('DL-0420110099')).toBeInTheDocument();
    expect(screen.getByText('9876543210')).toBeInTheDocument();
  });

  it('5. Switches to Routes tab and opens Manage Stops modal', async () => {
    render(<TransportPage />);

    const routesTab = await screen.findByText('Transit Routes & Stops');
    fireEvent.click(routesTab);

    expect(await screen.findByText('R-NORTH-1')).toBeInTheDocument();
    expect(screen.getByText('North Campus Express')).toBeInTheDocument();

    const manageStopsBtn = screen.getByText('Manage Stops');
    fireEvent.click(manageStopsBtn);

    expect(await screen.findByText(/Route Stops: R-NORTH-1/)).toBeInTheDocument();
    expect(screen.getByText('Jubilee Hills Checkpost')).toBeInTheDocument();
    expect(screen.getByText('Madhapur Metro')).toBeInTheDocument();
  });

  it('6. Switches to Allocations tab and renders student allocations', async () => {
    render(<TransportPage />);

    const allocTab = await screen.findByText('Student Allocations');
    fireEvent.click(allocTab);

    expect(await screen.findByText('Aarav Sharma')).toBeInTheDocument();
    expect(screen.getByText('ADM-101')).toBeInTheDocument();
    expect(screen.getByText('TWO WAY')).toBeInTheDocument();
  });

  it('7. Handles allocation status update modal (ACTIVE -> SUSPENDED)', async () => {
    vi.mocked(transportApi.updateAllocationStatus).mockResolvedValue({
      ...mockAllocationsList.items[0],
      status: 'SUSPENDED',
    });

    render(<TransportPage />);

    const allocTab = await screen.findByRole('button', { name: /Student Allocations/i });
    fireEvent.click(allocTab);

    expect(await screen.findByText('Aarav Sharma')).toBeInTheDocument();

    const statusBtn = screen.getByRole('button', { name: 'Status' });
    fireEvent.click(statusBtn);

    expect(await screen.findByText(/Update Allocation Status: Aarav Sharma/)).toBeInTheDocument();

    const updateBtn = screen.getByRole('button', { name: 'Update Status' });
    fireEvent.click(updateBtn);

    await waitFor(() => {
      expect(transportApi.updateAllocationStatus).toHaveBeenCalledWith(
        'alloc-1',
        expect.objectContaining({
          status: 'SUSPENDED',
        })
      );
    });
  });

  it('8. Enforces RBAC: View-only user cannot see create/edit/delete buttons', async () => {
    useAuthStore.setState({
      user: { id: 'usr-view', email: 'viewer@school.com', is_super_admin: false } as any,
      permissions: ['transport.view'],
      roles: [{ id: 'r2', name: 'TEACHER', code: 'TEACHER' }],
      isAuthenticated: true,
    });

    render(<TransportPage />);

    const fleetTab = await screen.findByText('Fleet Management');
    fireEvent.click(fleetTab);

    expect(screen.queryByText('Add Vehicle')).not.toBeInTheDocument();
    expect(screen.queryByTitle('Edit Vehicle')).not.toBeInTheDocument();
    expect(screen.queryByTitle('Delete Vehicle')).not.toBeInTheDocument();
  });
});
