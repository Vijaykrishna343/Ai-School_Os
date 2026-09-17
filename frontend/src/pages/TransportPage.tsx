import React, { useEffect, useState } from 'react';
import {
  Bus,
  Users,
  MapPin,
  Route as RouteIcon,
  Plus,
  Search,
  RefreshCw,
  Edit2,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  Phone,
  Calendar,
  TrendingUp,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { transportApi } from '@/services/api/transportApi';
import { academicYearsApi } from '@/services/api/academicYearsApi';
import { studentsApi } from '@/services/api/studentsApi';
import { teachersApi } from '@/services/api/teachersApi';
import {
  AcademicYear,
  FuelType,
  RouteStop,
  RouteStopCreate,
  Student,
  StudentTransportAllocation,
  StudentTransportAllocationCreate,
  Teacher,
  TransportAllocationStatus,
  TransportAllocationType,
  TransportDashboardStats,
  TransportDriver,
  TransportDriverCreate,
  TransportRoute,
  TransportRouteCreate,
  TransportVehicle,
  TransportVehicleCreate,
  VehicleStatus,
  VehicleType,
} from '@/types/models';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Pagination } from '@/components/ui/Pagination';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { LoadingState } from '@/components/ui/LoadingState';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Alert } from '@/components/ui/Alert';

export const TransportPage: React.FC = () => {
  const { user, permissions, roles } = useAuthStore();
  const isSuperAdmin =
    user?.is_super_admin ||
    roles?.some((r: any) => r.name === 'Super Admin' || r.name === 'SUPER_ADMIN');

  const hasPermission = (perm: string) => isSuperAdmin || permissions.includes(perm);

  const canCreate = hasPermission('transport.create');
  const canUpdate = hasPermission('transport.update');
  const canDelete = hasPermission('transport.delete');
  const canAllocate = hasPermission('transport.allocate');

  // Active Tab
  const [activeTab, setActiveTab] = useState<'dashboard' | 'vehicles' | 'drivers' | 'routes' | 'allocations'>('dashboard');

  // Shared Reference Data
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [selectedAcademicYearId, setSelectedAcademicYearId] = useState<string>('');
  const [teachersList, setTeachersList] = useState<Teacher[]>([]);

  // --------------------------------------------------------------------------
  // Dashboard State
  // --------------------------------------------------------------------------
  const [dashboardStats, setDashboardStats] = useState<TransportDashboardStats | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  // --------------------------------------------------------------------------
  // Vehicles State
  // --------------------------------------------------------------------------
  const [vehicles, setVehicles] = useState<TransportVehicle[]>([]);
  const [vehicleSearch, setVehicleSearch] = useState('');
  const [vehicleStatusFilter, setVehicleStatusFilter] = useState<string>('');
  const [vehicleTypeFilter, setVehicleTypeFilter] = useState<string>('');
  const [vehiclePage, setVehiclePage] = useState(1);
  const [vehicleTotalPages, setVehicleTotalPages] = useState(1);
  const [loadingVehicles, setLoadingVehicles] = useState(false);
  const [vehicleError, setVehicleError] = useState<string | null>(null);

  const [showVehicleModal, setShowVehicleModal] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<TransportVehicle | null>(null);
  const [vehicleFormData, setVehicleFormData] = useState<TransportVehicleCreate>({
    registration_number: '',
    vehicle_code: '',
    vehicle_type: 'BUS',
    seating_capacity: 30,
    fuel_type: 'DIESEL',
    insurance_expiry_date: '',
    fitness_expiry_date: '',
    gps_device_id: '',
    status: 'ACTIVE',
    description: '',
  });
  const [vehicleFormError, setVehicleFormError] = useState<string | null>(null);
  const [submittingVehicle, setSubmittingVehicle] = useState(false);
  const [deletingVehicleId, setDeletingVehicleId] = useState<string | null>(null);

  // --------------------------------------------------------------------------
  // Drivers State
  // --------------------------------------------------------------------------
  const [drivers, setDrivers] = useState<TransportDriver[]>([]);
  const [driverSearch, setDriverSearch] = useState('');
  const [driverActiveFilter, setDriverActiveFilter] = useState<string>('');
  const [driverPage, setDriverPage] = useState(1);
  const [driverTotalPages, setDriverTotalPages] = useState(1);
  const [loadingDrivers, setLoadingDrivers] = useState(false);
  const [driverError, setDriverError] = useState<string | null>(null);

  const [showDriverModal, setShowDriverModal] = useState(false);
  const [editingDriver, setEditingDriver] = useState<TransportDriver | null>(null);
  const [driverFormData, setDriverFormData] = useState<TransportDriverCreate>({
    driver_name: '',
    license_number: '',
    license_expiry_date: '',
    contact_phone: '',
    emergency_contact: '',
    address: '',
    is_active: true,
    staff_id: '',
  });
  const [driverFormError, setDriverFormError] = useState<string | null>(null);
  const [submittingDriver, setSubmittingDriver] = useState(false);
  const [deletingDriverId, setDeletingDriverId] = useState<string | null>(null);

  // --------------------------------------------------------------------------
  // Routes State
  // --------------------------------------------------------------------------
  const [routes, setRoutes] = useState<TransportRoute[]>([]);
  const [routeSearch, setRouteSearch] = useState('');
  const [routeActiveFilter, setRouteActiveFilter] = useState<string>('');
  const [routePage, setRoutePage] = useState(1);
  const [routeTotalPages, setRouteTotalPages] = useState(1);
  const [loadingRoutes, setLoadingRoutes] = useState(false);
  const [routeError, setRouteError] = useState<string | null>(null);

  const [showRouteModal, setShowRouteModal] = useState(false);
  const [editingRoute, setEditingRoute] = useState<TransportRoute | null>(null);
  const [routeFormData, setRouteFormData] = useState<TransportRouteCreate>({
    route_code: '',
    route_name: '',
    description: '',
    vehicle_id: '',
    driver_id: '',
    attendant_name: '',
    attendant_phone: '',
    morning_start_time: '07:30',
    evening_start_time: '15:30',
    is_active: true,
  });
  const [routeFormError, setRouteFormError] = useState<string | null>(null);
  const [submittingRoute, setSubmittingRoute] = useState(false);
  const [deletingRouteId, setDeletingRouteId] = useState<string | null>(null);

  // Route Stops Management (Detail Drawer/Modal)
  const [selectedRouteForStops, setSelectedRouteForStops] = useState<TransportRoute | null>(null);
  const [routeStops, setRouteStops] = useState<RouteStop[]>([]);
  const [loadingRouteStops, setLoadingRouteStops] = useState(false);
  const [routeStopsError, setRouteStopsError] = useState<string | null>(null);

  const [showStopModal, setShowStopModal] = useState(false);
  const [editingStop, setEditingStop] = useState<RouteStop | null>(null);
  const [stopFormData, setStopFormData] = useState<RouteStopCreate>({
    stop_name: '',
    stop_code: '',
    sequence_order: 1,
    morning_pickup_time: '07:45',
    afternoon_drop_time: '16:00',
    landmark: '',
    pickup_fee_amount: '500.00',
    is_active: true,
  });
  const [stopFormError, setStopFormError] = useState<string | null>(null);
  const [submittingStop, setSubmittingStop] = useState(false);
  const [deletingStopId, setDeletingStopId] = useState<string | null>(null);

  // --------------------------------------------------------------------------
  // Allocations State
  // --------------------------------------------------------------------------
  const [allocations, setAllocations] = useState<StudentTransportAllocation[]>([]);
  const [allocationSearch, setAllocationSearch] = useState('');
  const [allocationRouteFilter, setAllocationRouteFilter] = useState<string>('');
  const [allocationStatusFilter, setAllocationStatusFilter] = useState<string>('');
  const [allocationPage, setAllocationPage] = useState(1);
  const [allocationTotalPages, setAllocationTotalPages] = useState(1);
  const [loadingAllocations, setLoadingAllocations] = useState(false);
  const [allocationError, setAllocationError] = useState<string | null>(null);

  const [showAllocationModal, setShowAllocationModal] = useState(false);
  const [allocationFormData, setAllocationFormData] = useState<StudentTransportAllocationCreate>({
    student_id: '',
    route_id: '',
    academic_year_id: '',
    allocation_type: 'TWO_WAY',
    pickup_stop_id: '',
    drop_stop_id: '',
    status: 'ACTIVE',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    remarks: '',
  });
  const [selectedRouteStopsForAllocation, setSelectedRouteStopsForAllocation] = useState<RouteStop[]>([]);
  const [allocationFormError, setAllocationFormError] = useState<string | null>(null);
  const [submittingAllocation, setSubmittingAllocation] = useState(false);

  // Student Search Options
  const [studentOptions, setStudentOptions] = useState<{ id: string; name: string; admission_number: string }[]>([]);
  const [searchingStudents, setSearchingStudents] = useState(false);

  // Status Change Modal
  const [statusTargetAllocation, setStatusTargetAllocation] = useState<StudentTransportAllocation | null>(null);
  const [newAllocationStatus, setNewAllocationStatus] = useState<TransportAllocationStatus>('SUSPENDED');
  const [statusRemarks, setStatusRemarks] = useState('');
  const [statusEndDate, setStatusEndDate] = useState('');
  const [submittingStatusChange, setSubmittingStatusChange] = useState(false);
  const [statusChangeError, setStatusChangeError] = useState<string | null>(null);
  const [deletingAllocationId, setDeletingAllocationId] = useState<string | null>(null);

  // General Notification / Alert
  const [successToast, setSuccessToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setSuccessToast(msg);
    setTimeout(() => setSuccessToast(null), 4000);
  };

  // --------------------------------------------------------------------------
  // Initial Reference Loading
  // --------------------------------------------------------------------------
  useEffect(() => {
    fetchAcademicYears();
    fetchTeachers();
  }, []);

  const fetchAcademicYears = async () => {
    try {
      const res = await academicYearsApi.getAcademicYears({ page_size: 50 });
      const items = Array.isArray(res) ? res : res.items || [];
      setAcademicYears(items);
      const active = items.find((ay: AcademicYear) => ay.status === 'ACTIVE' || ay.is_current);
      if (active) {
        setSelectedAcademicYearId(active.id);
        setAllocationFormData((prev) => ({ ...prev, academic_year_id: active.id }));
      } else if (items.length > 0) {
        setSelectedAcademicYearId(items[0].id);
        setAllocationFormData((prev) => ({ ...prev, academic_year_id: items[0].id }));
      }
    } catch (err) {
      console.error('Failed to load academic years:', err);
    }
  };

  const fetchTeachers = async () => {
    try {
      const res = await teachersApi.getTeachers({ page_size: 100 });
      setTeachersList(res.items || []);
    } catch (err) {
      console.error('Failed to load teachers for driver association:', err);
    }
  };

  // --------------------------------------------------------------------------
  // Tab-specific Fetch Triggers
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchDashboardStats();
    } else if (activeTab === 'vehicles') {
      fetchVehicles();
    } else if (activeTab === 'drivers') {
      fetchDrivers();
    } else if (activeTab === 'routes') {
      fetchRoutes();
      fetchVehiclesForOptions();
      fetchDriversForOptions();
    } else if (activeTab === 'allocations') {
      fetchAllocations();
      fetchRoutesForOptions();
    }
  }, [activeTab]);

  // --------------------------------------------------------------------------
  // 1. Dashboard Handlers
  // --------------------------------------------------------------------------
  const fetchDashboardStats = async () => {
    setLoadingDashboard(true);
    setDashboardError(null);
    try {
      const stats = await transportApi.getDashboardStats();
      setDashboardStats(stats);
    } catch (err: any) {
      setDashboardError(err.message || 'Failed to load transport dashboard statistics');
    } finally {
      setLoadingDashboard(false);
    }
  };

  // --------------------------------------------------------------------------
  // 2. Vehicles Handlers
  // --------------------------------------------------------------------------
  const fetchVehicles = async () => {
    setLoadingVehicles(true);
    setVehicleError(null);
    try {
      const res = await transportApi.getVehicles({
        search: vehicleSearch || undefined,
        status: vehicleStatusFilter || undefined,
        vehicle_type: vehicleTypeFilter || undefined,
        page: vehiclePage,
        page_size: 10,
      });
      setVehicles(res.items || []);
      setVehicleTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setVehicleError(err.message || 'Failed to fetch vehicles');
    } finally {
      setLoadingVehicles(false);
    }
  };

  const fetchVehiclesForOptions = async () => {
    try {
      const res = await transportApi.getVehicles({ page_size: 100, status: 'ACTIVE' });
      setVehicles(res.items || []);
    } catch (err) {
      console.error('Failed to load vehicle options:', err);
    }
  };

  const handleOpenCreateVehicle = () => {
    setEditingVehicle(null);
    setVehicleFormData({
      registration_number: '',
      vehicle_code: '',
      vehicle_type: 'BUS',
      seating_capacity: 30,
      fuel_type: 'DIESEL',
      insurance_expiry_date: '',
      fitness_expiry_date: '',
      gps_device_id: '',
      status: 'ACTIVE',
      description: '',
    });
    setVehicleFormError(null);
    setShowVehicleModal(true);
  };

  const handleOpenEditVehicle = (vehicle: TransportVehicle) => {
    setEditingVehicle(vehicle);
    setVehicleFormData({
      registration_number: vehicle.registration_number,
      vehicle_code: vehicle.vehicle_code,
      vehicle_type: vehicle.vehicle_type,
      seating_capacity: vehicle.seating_capacity,
      fuel_type: vehicle.fuel_type || 'DIESEL',
      insurance_expiry_date: vehicle.insurance_expiry_date || '',
      fitness_expiry_date: vehicle.fitness_expiry_date || '',
      gps_device_id: vehicle.gps_device_id || '',
      status: vehicle.status,
      description: vehicle.description || '',
    });
    setVehicleFormError(null);
    setShowVehicleModal(true);
  };

  const handleSaveVehicle = async (e: React.FormEvent) => {
    e.preventDefault();
    setVehicleFormError(null);
    if (!vehicleFormData.registration_number.trim()) {
      setVehicleFormError('Registration number is required.');
      return;
    }
    if (!vehicleFormData.vehicle_code.trim()) {
      setVehicleFormError('Vehicle code is required.');
      return;
    }
    if (Number(vehicleFormData.seating_capacity) < 1) {
      setVehicleFormError('Seating capacity must be at least 1.');
      return;
    }

    setSubmittingVehicle(true);
    try {
      if (editingVehicle) {
        await transportApi.updateVehicle(editingVehicle.id, {
          ...vehicleFormData,
          seating_capacity: Number(vehicleFormData.seating_capacity),
          insurance_expiry_date: vehicleFormData.insurance_expiry_date || null,
          fitness_expiry_date: vehicleFormData.fitness_expiry_date || null,
          gps_device_id: vehicleFormData.gps_device_id || null,
        });
        showToast(`Vehicle ${vehicleFormData.vehicle_code} updated successfully.`);
      } else {
        await transportApi.createVehicle({
          ...vehicleFormData,
          seating_capacity: Number(vehicleFormData.seating_capacity),
          insurance_expiry_date: vehicleFormData.insurance_expiry_date || null,
          fitness_expiry_date: vehicleFormData.fitness_expiry_date || null,
          gps_device_id: vehicleFormData.gps_device_id || null,
        });
        showToast(`Vehicle ${vehicleFormData.vehicle_code} created successfully.`);
      }
      setShowVehicleModal(false);
      fetchVehicles();
    } catch (err: any) {
      setVehicleFormError(err.message || 'Failed to save vehicle');
    } finally {
      setSubmittingVehicle(false);
    }
  };

  const handleDeleteVehicle = async () => {
    if (!deletingVehicleId) return;
    try {
      await transportApi.deleteVehicle(deletingVehicleId);
      showToast('Vehicle deleted successfully.');
      setDeletingVehicleId(null);
      fetchVehicles();
    } catch (err: any) {
      alert(err.message || 'Failed to delete vehicle');
      setDeletingVehicleId(null);
    }
  };

  // --------------------------------------------------------------------------
  // 3. Drivers Handlers
  // --------------------------------------------------------------------------
  const fetchDrivers = async () => {
    setLoadingDrivers(true);
    setDriverError(null);
    try {
      const res = await transportApi.getDrivers({
        search: driverSearch || undefined,
        is_active: driverActiveFilter === 'true' ? true : driverActiveFilter === 'false' ? false : undefined,
        page: driverPage,
        page_size: 10,
      });
      setDrivers(res.items || []);
      setDriverTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setDriverError(err.message || 'Failed to fetch drivers');
    } finally {
      setLoadingDrivers(false);
    }
  };

  const fetchDriversForOptions = async () => {
    try {
      const res = await transportApi.getDrivers({ page_size: 100, is_active: true });
      setDrivers(res.items || []);
    } catch (err) {
      console.error('Failed to load driver options:', err);
    }
  };

  const handleOpenCreateDriver = () => {
    setEditingDriver(null);
    setDriverFormData({
      driver_name: '',
      license_number: '',
      license_expiry_date: '',
      contact_phone: '',
      emergency_contact: '',
      address: '',
      is_active: true,
      staff_id: '',
    });
    setDriverFormError(null);
    setShowDriverModal(true);
  };

  const handleOpenEditDriver = (driver: TransportDriver) => {
    setEditingDriver(driver);
    setDriverFormData({
      driver_name: driver.driver_name,
      license_number: driver.license_number,
      license_expiry_date: driver.license_expiry_date || '',
      contact_phone: driver.contact_phone,
      emergency_contact: driver.emergency_contact || '',
      address: driver.address || '',
      is_active: driver.is_active,
      staff_id: driver.staff_id || '',
    });
    setDriverFormError(null);
    setShowDriverModal(true);
  };

  const handleSaveDriver = async (e: React.FormEvent) => {
    e.preventDefault();
    setDriverFormError(null);
    if (!driverFormData.driver_name.trim()) {
      setDriverFormError('Driver name is required.');
      return;
    }
    if (!driverFormData.license_number.trim()) {
      setDriverFormError('License number is required.');
      return;
    }
    if (!driverFormData.contact_phone.trim()) {
      setDriverFormError('Contact phone is required.');
      return;
    }

    setSubmittingDriver(true);
    try {
      if (editingDriver) {
        await transportApi.updateDriver(editingDriver.id, {
          ...driverFormData,
          license_expiry_date: driverFormData.license_expiry_date || null,
          emergency_contact: driverFormData.emergency_contact || null,
          address: driverFormData.address || null,
          staff_id: driverFormData.staff_id || null,
        });
        showToast(`Driver ${driverFormData.driver_name} updated successfully.`);
      } else {
        await transportApi.createDriver({
          ...driverFormData,
          license_expiry_date: driverFormData.license_expiry_date || null,
          emergency_contact: driverFormData.emergency_contact || null,
          address: driverFormData.address || null,
          staff_id: driverFormData.staff_id || null,
        });
        showToast(`Driver ${driverFormData.driver_name} created successfully.`);
      }
      setShowDriverModal(false);
      fetchDrivers();
    } catch (err: any) {
      setDriverFormError(err.message || 'Failed to save driver');
    } finally {
      setSubmittingDriver(false);
    }
  };

  const handleDeleteDriver = async () => {
    if (!deletingDriverId) return;
    try {
      await transportApi.deleteDriver(deletingDriverId);
      showToast('Driver deleted successfully.');
      setDeletingDriverId(null);
      fetchDrivers();
    } catch (err: any) {
      alert(err.message || 'Failed to delete driver');
      setDeletingDriverId(null);
    }
  };

  // --------------------------------------------------------------------------
  // 4. Routes & Stops Handlers
  // --------------------------------------------------------------------------
  const fetchRoutes = async () => {
    setLoadingRoutes(true);
    setRouteError(null);
    try {
      const res = await transportApi.getRoutes({
        search: routeSearch || undefined,
        is_active: routeActiveFilter === 'true' ? true : routeActiveFilter === 'false' ? false : undefined,
        page: routePage,
        page_size: 10,
      });
      setRoutes(res.items || []);
      setRouteTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setRouteError(err.message || 'Failed to fetch routes');
    } finally {
      setLoadingRoutes(false);
    }
  };

  const fetchRoutesForOptions = async () => {
    try {
      const res = await transportApi.getRoutes({ page_size: 100, is_active: true });
      setRoutes(res.items || []);
    } catch (err) {
      console.error('Failed to load route options:', err);
    }
  };

  const handleOpenCreateRoute = () => {
    setEditingRoute(null);
    setRouteFormData({
      route_code: '',
      route_name: '',
      description: '',
      vehicle_id: '',
      driver_id: '',
      attendant_name: '',
      attendant_phone: '',
      morning_start_time: '07:30',
      evening_start_time: '15:30',
      is_active: true,
    });
    setRouteFormError(null);
    setShowRouteModal(true);
  };

  const handleOpenEditRoute = (route: TransportRoute) => {
    setEditingRoute(route);
    setRouteFormData({
      route_code: route.route_code,
      route_name: route.route_name,
      description: route.description || '',
      vehicle_id: route.vehicle_id || '',
      driver_id: route.driver_id || '',
      attendant_name: route.attendant_name || '',
      attendant_phone: route.attendant_phone || '',
      morning_start_time: route.morning_start_time || '07:30',
      evening_start_time: route.evening_start_time || '15:30',
      is_active: route.is_active,
    });
    setRouteFormError(null);
    setShowRouteModal(true);
  };

  const handleSaveRoute = async (e: React.FormEvent) => {
    e.preventDefault();
    setRouteFormError(null);
    if (!routeFormData.route_code.trim()) {
      setRouteFormError('Route code is required.');
      return;
    }
    if (!routeFormData.route_name.trim()) {
      setRouteFormError('Route name is required.');
      return;
    }

    setSubmittingRoute(true);
    try {
      const payload: TransportRouteCreate = {
        ...routeFormData,
        vehicle_id: routeFormData.vehicle_id || null,
        driver_id: routeFormData.driver_id || null,
        description: routeFormData.description || null,
        attendant_name: routeFormData.attendant_name || null,
        attendant_phone: routeFormData.attendant_phone || null,
      };

      if (editingRoute) {
        await transportApi.updateRoute(editingRoute.id, payload);
        showToast(`Route ${routeFormData.route_code} updated successfully.`);
      } else {
        await transportApi.createRoute(payload);
        showToast(`Route ${routeFormData.route_code} created successfully.`);
      }
      setShowRouteModal(false);
      fetchRoutes();
    } catch (err: any) {
      setRouteFormError(err.message || 'Failed to save route');
    } finally {
      setSubmittingRoute(false);
    }
  };

  const handleDeleteRoute = async () => {
    if (!deletingRouteId) return;
    try {
      await transportApi.deleteRoute(deletingRouteId);
      showToast('Route deleted successfully.');
      setDeletingRouteId(null);
      fetchRoutes();
    } catch (err: any) {
      alert(err.message || 'Failed to delete route. Note: Active student allocations must be reallocated first.');
      setDeletingRouteId(null);
    }
  };

  // Stops Management within Route
  const handleOpenRouteStops = async (route: TransportRoute) => {
    setSelectedRouteForStops(route);
    setLoadingRouteStops(true);
    setRouteStopsError(null);
    try {
      const stops = await transportApi.getStops(route.id);
      setRouteStops(stops);
    } catch (err: any) {
      setRouteStopsError(err.message || 'Failed to fetch stops for this route');
    } finally {
      setLoadingRouteStops(false);
    }
  };

  const handleOpenCreateStop = () => {
    setEditingStop(null);
    const nextSeq = routeStops.length > 0 ? Math.max(...routeStops.map((s) => s.sequence_order)) + 1 : 1;
    setStopFormData({
      stop_name: '',
      stop_code: '',
      sequence_order: nextSeq,
      morning_pickup_time: '07:45',
      afternoon_drop_time: '16:00',
      landmark: '',
      pickup_fee_amount: '500.00',
      is_active: true,
    });
    setStopFormError(null);
    setShowStopModal(true);
  };

  const handleOpenEditStop = (stop: RouteStop) => {
    setEditingStop(stop);
    setStopFormData({
      stop_name: stop.stop_name,
      stop_code: stop.stop_code,
      sequence_order: stop.sequence_order,
      morning_pickup_time: stop.morning_pickup_time || '07:45',
      afternoon_drop_time: stop.afternoon_drop_time || '16:00',
      landmark: stop.landmark || '',
      pickup_fee_amount: String(stop.pickup_fee_amount),
      is_active: stop.is_active,
    });
    setStopFormError(null);
    setShowStopModal(true);
  };

  const handleSaveStop = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRouteForStops) return;
    setStopFormError(null);

    if (!stopFormData.stop_name.trim()) {
      setStopFormError('Stop name is required.');
      return;
    }
    if (!stopFormData.stop_code.trim()) {
      setStopFormError('Stop code is required.');
      return;
    }
    if (Number(stopFormData.sequence_order) < 1) {
      setStopFormError('Sequence order must be a positive integer.');
      return;
    }
    if (Number(stopFormData.pickup_fee_amount) < 0) {
      setStopFormError('Pickup fee cannot be negative.');
      return;
    }

    setSubmittingStop(true);
    try {
      const payload: RouteStopCreate = {
        ...stopFormData,
        sequence_order: Number(stopFormData.sequence_order),
        pickup_fee_amount: stopFormData.pickup_fee_amount,
        landmark: stopFormData.landmark || null,
        morning_pickup_time: stopFormData.morning_pickup_time || null,
        afternoon_drop_time: stopFormData.afternoon_drop_time || null,
      };

      if (editingStop) {
        await transportApi.updateStop(selectedRouteForStops.id, editingStop.id, payload);
        showToast(`Stop ${stopFormData.stop_name} updated.`);
      } else {
        await transportApi.createStop(selectedRouteForStops.id, payload);
        showToast(`Stop ${stopFormData.stop_name} added.`);
      }
      setShowStopModal(false);
      handleOpenRouteStops(selectedRouteForStops);
    } catch (err: any) {
      setStopFormError(err.message || 'Failed to save stop');
    } finally {
      setSubmittingStop(false);
    }
  };

  const handleDeleteStop = async () => {
    if (!selectedRouteForStops || !deletingStopId) return;
    try {
      await transportApi.deleteStop(selectedRouteForStops.id, deletingStopId);
      showToast('Stop deleted successfully.');
      setDeletingStopId(null);
      handleOpenRouteStops(selectedRouteForStops);
    } catch (err: any) {
      alert(err.message || 'Failed to delete stop. Note: Active student allocations may be using this stop.');
      setDeletingStopId(null);
    }
  };

  // --------------------------------------------------------------------------
  // 5. Allocations Handlers
  // --------------------------------------------------------------------------
  const fetchAllocations = async () => {
    setLoadingAllocations(true);
    setAllocationError(null);
    try {
      const res = await transportApi.getAllocations({
        search: allocationSearch || undefined,
        route_id: allocationRouteFilter || undefined,
        status: allocationStatusFilter || undefined,
        academic_year_id: selectedAcademicYearId || undefined,
        page: allocationPage,
        page_size: 10,
      });
      setAllocations(res.items || []);
      setAllocationTotalPages(res.total_pages || 1);
    } catch (err: any) {
      setAllocationError(err.message || 'Failed to fetch allocations');
    } finally {
      setLoadingAllocations(false);
    }
  };

  const searchStudents = async (query: string) => {
    if (!query.trim()) {
      setStudentOptions([]);
      return;
    }
    setSearchingStudents(true);
    try {
      const res = await studentsApi.getStudents({ search: query, page_size: 15 });
      setStudentOptions(
        (res.items || []).map((s: Student) => ({
          id: s.id,
          name: `${s.first_name} ${s.last_name}`,
          admission_number: s.admission_number || '',
        }))
      );
    } catch (err) {
      console.error('Failed to search students:', err);
    } finally {
      setSearchingStudents(false);
    }
  };

  const handleRouteChangeInAllocationForm = async (routeId: string) => {
    setAllocationFormData((prev) => ({
      ...prev,
      route_id: routeId,
      pickup_stop_id: '',
      drop_stop_id: '',
    }));
    if (!routeId) {
      setSelectedRouteStopsForAllocation([]);
      return;
    }
    try {
      const stops = await transportApi.getStops(routeId);
      setSelectedRouteStopsForAllocation(stops);
    } catch (err) {
      console.error('Failed to fetch stops for route:', err);
    }
  };

  const handleOpenCreateAllocation = () => {
    setAllocationFormData({
      student_id: '',
      route_id: '',
      academic_year_id: selectedAcademicYearId,
      allocation_type: 'TWO_WAY',
      pickup_stop_id: '',
      drop_stop_id: '',
      status: 'ACTIVE',
      start_date: new Date().toISOString().split('T')[0],
      end_date: '',
      remarks: '',
    });
    setSelectedRouteStopsForAllocation([]);
    setStudentOptions([]);
    setAllocationFormError(null);
    setShowAllocationModal(true);
  };

  const handleSaveAllocation = async (e: React.FormEvent) => {
    e.preventDefault();
    setAllocationFormError(null);

    if (!allocationFormData.student_id) {
      setAllocationFormError('Please select a student.');
      return;
    }
    if (!allocationFormData.route_id) {
      setAllocationFormError('Please select a route.');
      return;
    }
    if (!allocationFormData.academic_year_id) {
      setAllocationFormError('Academic Year is required.');
      return;
    }

    // Enforce type invariants on client before sending
    if (allocationFormData.allocation_type === 'TWO_WAY') {
      if (!allocationFormData.pickup_stop_id) {
        setAllocationFormError('Pickup stop is required for Two-Way allocation.');
        return;
      }
      if (!allocationFormData.drop_stop_id) {
        setAllocationFormError('Drop stop is required for Two-Way allocation.');
        return;
      }
    } else if (allocationFormData.allocation_type === 'PICKUP_ONLY') {
      if (!allocationFormData.pickup_stop_id) {
        setAllocationFormError('Pickup stop is required for Pickup Only allocation.');
        return;
      }
    } else if (allocationFormData.allocation_type === 'DROP_ONLY') {
      if (!allocationFormData.drop_stop_id) {
        setAllocationFormError('Drop stop is required for Drop Only allocation.');
        return;
      }
    }

    setSubmittingAllocation(true);
    try {
      const payload: StudentTransportAllocationCreate = {
        ...allocationFormData,
        pickup_stop_id:
          allocationFormData.allocation_type === 'DROP_ONLY' ? null : allocationFormData.pickup_stop_id || null,
        drop_stop_id:
          allocationFormData.allocation_type === 'PICKUP_ONLY' ? null : allocationFormData.drop_stop_id || null,
        end_date: allocationFormData.end_date || null,
        remarks: allocationFormData.remarks || null,
      };

      await transportApi.createAllocation(payload);
      showToast('Student allocated to transport route successfully.');
      setShowAllocationModal(false);
      fetchAllocations();
    } catch (err: any) {
      setAllocationFormError(err.message || 'Failed to create student allocation');
    } finally {
      setSubmittingAllocation(false);
    }
  };

  const handleOpenStatusModal = (allocation: StudentTransportAllocation) => {
    setStatusTargetAllocation(allocation);
    setNewAllocationStatus(allocation.status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE');
    setStatusRemarks(allocation.remarks || '');
    setStatusEndDate('');
    setStatusChangeError(null);
  };

  const handleSaveStatusChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!statusTargetAllocation) return;
    setStatusChangeError(null);
    setSubmittingStatusChange(true);
    try {
      await transportApi.updateAllocationStatus(statusTargetAllocation.id, {
        status: newAllocationStatus,
        remarks: statusRemarks || undefined,
        end_date: statusEndDate || undefined,
      });
      showToast(`Allocation status updated to ${newAllocationStatus}.`);
      setStatusTargetAllocation(null);
      fetchAllocations();
    } catch (err: any) {
      setStatusChangeError(err.message || 'Failed to update allocation status');
    } finally {
      setSubmittingStatusChange(false);
    }
  };

  const handleDeleteAllocation = async () => {
    if (!deletingAllocationId) return;
    try {
      await transportApi.deleteAllocation(deletingAllocationId);
      showToast('Allocation deleted successfully.');
      setDeletingAllocationId(null);
      fetchAllocations();
    } catch (err: any) {
      alert(err.message || 'Failed to delete allocation');
      setDeletingAllocationId(null);
    }
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Toast Banner */}
      {successToast && (
        <Alert type="success" className="animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>{successToast}</span>
          </div>
        </Alert>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2.5">
            <Bus className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            Transport Fleet & Logistics
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Manage school buses, certified drivers, transit routes, stops, and student passenger allocations.
          </p>
        </div>

        {/* Global Academic Year Selector & Action Buttons */}
        <div className="flex items-center flex-wrap gap-2">
          {academicYears.length > 0 && (
            <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-2.5 py-1 text-xs">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={selectedAcademicYearId}
                onChange={(e) => {
                  setSelectedAcademicYearId(e.target.value);
                  if (activeTab === 'allocations') {
                    fetchAllocations();
                  }
                }}
                className="bg-transparent border-none text-xs font-medium focus:ring-0 text-slate-700 dark:text-slate-200"
              >
                {academicYears.map((ay) => (
                  <option key={ay.id} value={ay.id}>
                    {ay.name} {ay.status === 'ACTIVE' ? '(Current)' : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          {activeTab === 'vehicles' && canCreate && (
            <Button onClick={handleOpenCreateVehicle} className="flex items-center gap-1.5">
              <Plus className="w-4 h-4" /> Add Vehicle
            </Button>
          )}

          {activeTab === 'drivers' && canCreate && (
            <Button onClick={handleOpenCreateDriver} className="flex items-center gap-1.5">
              <Plus className="w-4 h-4" /> Add Driver
            </Button>
          )}

          {activeTab === 'routes' && canCreate && (
            <Button onClick={handleOpenCreateRoute} className="flex items-center gap-1.5">
              <Plus className="w-4 h-4" /> Create Route
            </Button>
          )}

          {activeTab === 'allocations' && canAllocate && (
            <Button onClick={handleOpenCreateAllocation} className="flex items-center gap-1.5">
              <Plus className="w-4 h-4" /> New Allocation
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 gap-2 md:gap-6 overflow-x-auto">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`pb-3 font-medium text-xs md:text-sm border-b-2 whitespace-nowrap flex items-center gap-2 ${
            activeTab === 'dashboard'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
          }`}
        >
          <TrendingUp className="w-4 h-4" /> Dashboard Overview
        </button>
        <button
          onClick={() => setActiveTab('vehicles')}
          className={`pb-3 font-medium text-xs md:text-sm border-b-2 whitespace-nowrap flex items-center gap-2 ${
            activeTab === 'vehicles'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
          }`}
        >
          <Bus className="w-4 h-4" /> Fleet Management
        </button>
        <button
          onClick={() => setActiveTab('drivers')}
          className={`pb-3 font-medium text-xs md:text-sm border-b-2 whitespace-nowrap flex items-center gap-2 ${
            activeTab === 'drivers'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
          }`}
        >
          <Users className="w-4 h-4" /> Drivers Directory
        </button>
        <button
          onClick={() => setActiveTab('routes')}
          className={`pb-3 font-medium text-xs md:text-sm border-b-2 whitespace-nowrap flex items-center gap-2 ${
            activeTab === 'routes'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
          }`}
        >
          <RouteIcon className="w-4 h-4" /> Transit Routes & Stops
        </button>
        <button
          onClick={() => setActiveTab('allocations')}
          className={`pb-3 font-medium text-xs md:text-sm border-b-2 whitespace-nowrap flex items-center gap-2 ${
            activeTab === 'allocations'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
          }`}
        >
          <Users className="w-4 h-4" /> Student Allocations
        </button>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 1. DASHBOARD TAB                                                     */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {loadingDashboard && <LoadingState message="Loading transport dashboard analytics..." />}
          {dashboardError && <ErrorState message={dashboardError} onRetry={fetchDashboardStats} />}

          {!loadingDashboard && !dashboardError && dashboardStats && (
            <>
              {/* Primary KPI Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        Fleet Vehicles
                      </p>
                      <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                        {dashboardStats.active_vehicles}{' '}
                        <span className="text-xs font-normal text-slate-500">/ {dashboardStats.total_vehicles}</span>
                      </h3>
                      <p className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-0.5">
                        {dashboardStats.maintenance_vehicles} in maintenance
                      </p>
                    </div>
                    <div className="p-3 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400">
                      <Bus className="w-6 h-6" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        Active Drivers
                      </p>
                      <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                        {dashboardStats.active_drivers}
                      </h3>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Total {dashboardStats.total_drivers} registered
                      </p>
                    </div>
                    <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400">
                      <Users className="w-6 h-6" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        Transit Routes
                      </p>
                      <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                        {dashboardStats.active_routes}{' '}
                        <span className="text-xs font-normal text-slate-500">/ {dashboardStats.total_routes}</span>
                      </h3>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        {dashboardStats.total_stops} stops mapped
                      </p>
                    </div>
                    <div className="p-3 bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400">
                      <RouteIcon className="w-6 h-6" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        Student Allocations
                      </p>
                      <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                        {dashboardStats.active_allocations}
                      </h3>
                      <p className="text-[11px] text-indigo-600 dark:text-indigo-400 mt-0.5">
                        {dashboardStats.overall_occupancy_rate_percent}% fleet capacity
                      </p>
                    </div>
                    <div className="p-3 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400">
                      <Users className="w-6 h-6" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Seating Capacity Visualization */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center justify-between">
                    <span>Fleet Seating & Capacity Distribution</span>
                    <Badge variant="default">
                      {dashboardStats.total_occupied_seats} / {dashboardStats.total_seating_capacity} Seats Occupied
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Progress Bar */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-slate-500">
                      <span>Occupancy: {dashboardStats.overall_occupancy_rate_percent}%</span>
                      <span>{dashboardStats.total_available_seats} Available Seats</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-3 overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          dashboardStats.overall_occupancy_rate_percent > 90
                            ? 'bg-red-500'
                            : dashboardStats.overall_occupancy_rate_percent > 70
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(dashboardStats.overall_occupancy_rate_percent, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Vehicle Breakdown Table */}
                  {dashboardStats.vehicles_occupancy.length > 0 && (
                    <div className="overflow-x-auto pt-2 border border-slate-200 dark:border-slate-800">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
                          <tr>
                            <th className="px-3 py-2 font-semibold">Vehicle Code</th>
                            <th className="px-3 py-2 font-semibold">Registration</th>
                            <th className="px-3 py-2 font-semibold">Capacity</th>
                            <th className="px-3 py-2 font-semibold">Allocated</th>
                            <th className="px-3 py-2 font-semibold">Available</th>
                            <th className="px-3 py-2 font-semibold">Occupancy</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                          {dashboardStats.vehicles_occupancy.map((v) => (
                            <tr key={v.vehicle_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                              <td className="px-3 py-2 font-semibold">{v.vehicle_code}</td>
                              <td className="px-3 py-2 font-mono">{v.registration_number}</td>
                              <td className="px-3 py-2">{v.seating_capacity} seats</td>
                              <td className="px-3 py-2">{v.total_allocated_seats}</td>
                              <td className="px-3 py-2 font-mono text-slate-600 dark:text-slate-300">
                                {v.available_seats}
                              </td>
                              <td className="px-3 py-2">
                                <div className="flex items-center gap-2">
                                  <div className="w-20 bg-slate-100 dark:bg-slate-800 h-2 overflow-hidden">
                                    <div
                                      className={`h-full ${
                                        v.occupancy_rate_percent >= 100
                                          ? 'bg-red-500'
                                          : v.occupancy_rate_percent >= 80
                                          ? 'bg-amber-500'
                                          : 'bg-emerald-500'
                                      }`}
                                      style={{ width: `${Math.min(v.occupancy_rate_percent, 100)}%` }}
                                    />
                                  </div>
                                  <span className="text-[11px] font-mono">{v.occupancy_rate_percent}%</span>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* 2. FLEET MANAGEMENT TAB                                              */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === 'vehicles' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2 w-full md:w-auto">
              <div className="relative flex-1 md:w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search registration or code..."
                  value={vehicleSearch}
                  onChange={(e) => setVehicleSearch(e.target.value)}
                  className="pl-8 text-xs h-9"
                />
              </div>

              <select
                value={vehicleStatusFilter}
                onChange={(e) => setVehicleStatusFilter(e.target.value)}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs h-9 px-2.5 focus:ring-0"
              >
                <option value="">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="MAINTENANCE">Maintenance</option>
                <option value="DECOMMISSIONED">Decommissioned</option>
              </select>

              <select
                value={vehicleTypeFilter}
                onChange={(e) => setVehicleTypeFilter(e.target.value)}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs h-9 px-2.5 focus:ring-0"
              >
                <option value="">All Types</option>
                <option value="BUS">Bus</option>
                <option value="VAN">Van</option>
                <option value="MINIBUS">Minibus</option>
                <option value="AUTO">Auto</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <Button variant="outline" size="sm" onClick={fetchVehicles} className="flex items-center gap-1.5">
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </Button>
          </div>

          {loadingVehicles && <LoadingState message="Loading fleet vehicles..." />}
          {vehicleError && <ErrorState message={vehicleError} onRetry={fetchVehicles} />}

          {!loadingVehicles && !vehicleError && vehicles.length === 0 && (
            <EmptyState
              icon={<Bus className="w-10 h-10 text-slate-400" />}
              title="No Vehicles Found"
              description="Register fleet buses and vans to begin mapping school transport routes."
              action={
                canCreate ? (
                  <Button onClick={handleOpenCreateVehicle} className="mt-2">
                    <Plus className="w-4 h-4 mr-1.5" /> Add First Vehicle
                  </Button>
                ) : undefined
              }
            />
          )}

          {!loadingVehicles && !vehicleError && vehicles.length > 0 && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-3 py-2.5 font-semibold">Vehicle Code</th>
                    <th className="px-3 py-2.5 font-semibold">Registration</th>
                    <th className="px-3 py-2.5 font-semibold">Type</th>
                    <th className="px-3 py-2.5 font-semibold">Capacity</th>
                    <th className="px-3 py-2.5 font-semibold">Fuel</th>
                    <th className="px-3 py-2.5 font-semibold">Status</th>
                    <th className="px-3 py-2.5 font-semibold">Insurance Expiry</th>
                    <th className="px-3 py-2.5 font-semibold">Fitness Expiry</th>
                    <th className="px-3 py-2.5 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {vehicles.map((v) => (
                    <tr key={v.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-3 py-2.5 font-semibold text-indigo-600 dark:text-indigo-400">
                        {v.vehicle_code}
                      </td>
                      <td className="px-3 py-2.5 font-mono">{v.registration_number}</td>
                      <td className="px-3 py-2.5">{v.vehicle_type}</td>
                      <td className="px-3 py-2.5 font-semibold">{v.seating_capacity} seats</td>
                      <td className="px-3 py-2.5">{v.fuel_type || '—'}</td>
                      <td className="px-3 py-2.5">
                        <Badge
                          variant={
                            v.status === 'ACTIVE'
                              ? 'success'
                              : v.status === 'MAINTENANCE'
                              ? 'warning'
                              : 'default'
                          }
                        >
                          {v.status}
                        </Badge>
                      </td>
                      <td className="px-3 py-2.5">{v.insurance_expiry_date || '—'}</td>
                      <td className="px-3 py-2.5">{v.fitness_expiry_date || '—'}</td>
                      <td className="px-3 py-2.5 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {canUpdate && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleOpenEditVehicle(v)}
                              className="h-7 w-7 p-0"
                              title="Edit Vehicle"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                          {canDelete && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setDeletingVehicleId(v.id)}
                              className="h-7 w-7 p-0 text-red-600 hover:text-red-700"
                              title="Delete Vehicle"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="p-3 border-t border-slate-200 dark:border-slate-800">
                <Pagination page={vehiclePage} totalPages={vehicleTotalPages} onPageChange={setVehiclePage} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* 3. DRIVERS TAB                                                       */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === 'drivers' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2 w-full md:w-auto">
              <div className="relative flex-1 md:w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search driver name or license..."
                  value={driverSearch}
                  onChange={(e) => setDriverSearch(e.target.value)}
                  className="pl-8 text-xs h-9"
                />
              </div>

              <select
                value={driverActiveFilter}
                onChange={(e) => setDriverActiveFilter(e.target.value)}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs h-9 px-2.5 focus:ring-0"
              >
                <option value="">All Statuses</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>

            <Button variant="outline" size="sm" onClick={fetchDrivers} className="flex items-center gap-1.5">
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </Button>
          </div>

          {loadingDrivers && <LoadingState message="Loading drivers directory..." />}
          {driverError && <ErrorState message={driverError} onRetry={fetchDrivers} />}

          {!loadingDrivers && !driverError && drivers.length === 0 && (
            <EmptyState
              icon={<Users className="w-10 h-10 text-slate-400" />}
              title="No Drivers Found"
              description="Register licensed transport drivers to assign them to school routes."
              action={
                canCreate ? (
                  <Button onClick={handleOpenCreateDriver} className="mt-2">
                    <Plus className="w-4 h-4 mr-1.5" /> Add First Driver
                  </Button>
                ) : undefined
              }
            />
          )}

          {!loadingDrivers && !driverError && drivers.length > 0 && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-3 py-2.5 font-semibold">Driver Name</th>
                    <th className="px-3 py-2.5 font-semibold">License Number</th>
                    <th className="px-3 py-2.5 font-semibold">License Expiry</th>
                    <th className="px-3 py-2.5 font-semibold">Contact Phone</th>
                    <th className="px-3 py-2.5 font-semibold">Emergency Phone</th>
                    <th className="px-3 py-2.5 font-semibold">Status</th>
                    <th className="px-3 py-2.5 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {drivers.map((d) => (
                    <tr key={d.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-3 py-2.5 font-semibold">{d.driver_name}</td>
                      <td className="px-3 py-2.5 font-mono">{d.license_number}</td>
                      <td className="px-3 py-2.5">{d.license_expiry_date || '—'}</td>
                      <td className="px-3 py-2.5">{d.contact_phone}</td>
                      <td className="px-3 py-2.5">{d.emergency_contact || '—'}</td>
                      <td className="px-3 py-2.5">
                        <Badge variant={d.is_active ? 'success' : 'default'}>
                          {d.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {canUpdate && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleOpenEditDriver(d)}
                              className="h-7 w-7 p-0"
                              title="Edit Driver"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                          {canDelete && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setDeletingDriverId(d.id)}
                              className="h-7 w-7 p-0 text-red-600 hover:text-red-700"
                              title="Delete Driver"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="p-3 border-t border-slate-200 dark:border-slate-800">
                <Pagination page={driverPage} totalPages={driverTotalPages} onPageChange={setDriverPage} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* 4. ROUTES TAB                                                        */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === 'routes' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2 w-full md:w-auto">
              <div className="relative flex-1 md:w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search route code or name..."
                  value={routeSearch}
                  onChange={(e) => setRouteSearch(e.target.value)}
                  className="pl-8 text-xs h-9"
                />
              </div>

              <select
                value={routeActiveFilter}
                onChange={(e) => setRouteActiveFilter(e.target.value)}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs h-9 px-2.5 focus:ring-0"
              >
                <option value="">All Statuses</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>

            <Button variant="outline" size="sm" onClick={fetchRoutes} className="flex items-center gap-1.5">
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </Button>
          </div>

          {loadingRoutes && <LoadingState message="Loading transit routes..." />}
          {routeError && <ErrorState message={routeError} onRetry={fetchRoutes} />}

          {!loadingRoutes && !routeError && routes.length === 0 && (
            <EmptyState
              icon={<RouteIcon className="w-10 h-10 text-slate-400" />}
              title="No Transit Routes Found"
              description="Create school bus transit routes and map pickup stops."
              action={
                canCreate ? (
                  <Button onClick={handleOpenCreateRoute} className="mt-2">
                    <Plus className="w-4 h-4 mr-1.5" /> Create First Route
                  </Button>
                ) : undefined
              }
            />
          )}

          {!loadingRoutes && !routeError && routes.length > 0 && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-3 py-2.5 font-semibold">Route Code</th>
                    <th className="px-3 py-2.5 font-semibold">Route Name</th>
                    <th className="px-3 py-2.5 font-semibold">Assigned Vehicle</th>
                    <th className="px-3 py-2.5 font-semibold">Assigned Driver</th>
                    <th className="px-3 py-2.5 font-semibold">Morning Schedule</th>
                    <th className="px-3 py-2.5 font-semibold">Evening Schedule</th>
                    <th className="px-3 py-2.5 font-semibold">Status</th>
                    <th className="px-3 py-2.5 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {routes.map((r) => {
                    const assignedVehicle = vehicles.find((v) => v.id === r.vehicle_id);
                    const assignedDriver = drivers.find((d) => d.id === r.driver_id);
                    return (
                      <tr key={r.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="px-3 py-2.5 font-semibold text-indigo-600 dark:text-indigo-400">
                          {r.route_code}
                        </td>
                        <td className="px-3 py-2.5 font-medium">{r.route_name}</td>
                        <td className="px-3 py-2.5">
                          {assignedVehicle ? (
                            <span className="font-mono">
                              {assignedVehicle.vehicle_code} ({assignedVehicle.seating_capacity} seats)
                            </span>
                          ) : (
                            <span className="text-slate-400 italic">Unassigned</span>
                          )}
                        </td>
                        <td className="px-3 py-2.5">
                          {assignedDriver ? assignedDriver.driver_name : <span className="text-slate-400 italic">Unassigned</span>}
                        </td>
                        <td className="px-3 py-2.5 font-mono">{r.morning_start_time || '—'}</td>
                        <td className="px-3 py-2.5 font-mono">{r.evening_start_time || '—'}</td>
                        <td className="px-3 py-2.5">
                          <Badge variant={r.is_active ? 'success' : 'default'}>
                            {r.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </td>
                        <td className="px-3 py-2.5 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleOpenRouteStops(r)}
                              className="h-7 text-xs flex items-center gap-1"
                            >
                              <MapPin className="w-3.5 h-3.5" /> Manage Stops
                            </Button>
                            {canUpdate && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenEditRoute(r)}
                                className="h-7 w-7 p-0"
                                title="Edit Route"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </Button>
                            )}
                            {canDelete && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setDeletingRouteId(r.id)}
                                className="h-7 w-7 p-0 text-red-600 hover:text-red-700"
                                title="Delete Route"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <div className="p-3 border-t border-slate-200 dark:border-slate-800">
                <Pagination page={routePage} totalPages={routeTotalPages} onPageChange={setRoutePage} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* 5. ALLOCATIONS TAB                                                   */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === 'allocations' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center flex-wrap gap-2 w-full md:w-auto">
              <div className="relative flex-1 md:w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search student or route..."
                  value={allocationSearch}
                  onChange={(e) => setAllocationSearch(e.target.value)}
                  className="pl-8 text-xs h-9"
                />
              </div>

              <select
                value={allocationRouteFilter}
                onChange={(e) => setAllocationRouteFilter(e.target.value)}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs h-9 px-2.5 focus:ring-0"
              >
                <option value="">All Routes</option>
                {routes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.route_code} - {r.route_name}
                  </option>
                ))}
              </select>

              <select
                value={allocationStatusFilter}
                onChange={(e) => setAllocationStatusFilter(e.target.value)}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs h-9 px-2.5 focus:ring-0"
              >
                <option value="">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="SUSPENDED">Suspended</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>

            <Button variant="outline" size="sm" onClick={fetchAllocations} className="flex items-center gap-1.5">
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </Button>
          </div>

          {loadingAllocations && <LoadingState message="Loading passenger allocations..." />}
          {allocationError && <ErrorState message={allocationError} onRetry={fetchAllocations} />}

          {!loadingAllocations && !allocationError && allocations.length === 0 && (
            <EmptyState
              icon={<Users className="w-10 h-10 text-slate-400" />}
              title="No Transport Allocations"
              description="Allocate students to transit routes for daily pickup and drop."
              action={
                canAllocate ? (
                  <Button onClick={handleOpenCreateAllocation} className="mt-2">
                    <Plus className="w-4 h-4 mr-1.5" /> New Student Allocation
                  </Button>
                ) : undefined
              }
            />
          )}

          {!loadingAllocations && !allocationError && allocations.length > 0 && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-3 py-2.5 font-semibold">Student</th>
                    <th className="px-3 py-2.5 font-semibold">Admission No.</th>
                    <th className="px-3 py-2.5 font-semibold">Route</th>
                    <th className="px-3 py-2.5 font-semibold">Type</th>
                    <th className="px-3 py-2.5 font-semibold">Pickup Stop</th>
                    <th className="px-3 py-2.5 font-semibold">Drop Stop</th>
                    <th className="px-3 py-2.5 font-semibold">Status</th>
                    <th className="px-3 py-2.5 font-semibold">Start Date</th>
                    <th className="px-3 py-2.5 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {allocations.map((a) => (
                    <tr key={a.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-3 py-2.5 font-semibold">{a.student_name || a.student_id}</td>
                      <td className="px-3 py-2.5 font-mono">{a.admission_number || '—'}</td>
                      <td className="px-3 py-2.5 font-medium text-indigo-600 dark:text-indigo-400">
                        {a.route_code || a.route_id}
                      </td>
                      <td className="px-3 py-2.5">
                        <Badge variant="default" className="text-[10px]">
                          {a.allocation_type.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td className="px-3 py-2.5">{a.pickup_stop_name || (a.pickup_stop_id ? 'Assigned' : '—')}</td>
                      <td className="px-3 py-2.5">{a.drop_stop_name || (a.drop_stop_id ? 'Assigned' : '—')}</td>
                      <td className="px-3 py-2.5">
                        <Badge
                          variant={
                            a.status === 'ACTIVE'
                              ? 'success'
                              : a.status === 'SUSPENDED'
                              ? 'warning'
                              : 'error'
                          }
                        >
                          {a.status}
                        </Badge>
                      </td>
                      <td className="px-3 py-2.5 font-mono">{a.start_date}</td>
                      <td className="px-3 py-2.5 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {canAllocate && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleOpenStatusModal(a)}
                              className="h-7 text-[11px] px-2"
                            >
                              Status
                            </Button>
                          )}
                          {canDelete && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setDeletingAllocationId(a.id)}
                              className="h-7 w-7 p-0 text-red-600 hover:text-red-700"
                              title="Delete Allocation"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="p-3 border-t border-slate-200 dark:border-slate-800">
                <Pagination page={allocationPage} totalPages={allocationTotalPages} onPageChange={setAllocationPage} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* MODAL: CREATE / EDIT VEHICLE                                         */}
      {/* -------------------------------------------------------------------- */}
      {showVehicleModal && (
        <Modal
          isOpen={showVehicleModal}
          onClose={() => setShowVehicleModal(false)}
          title={editingVehicle ? `Edit Vehicle: ${editingVehicle.vehicle_code}` : 'Add New Fleet Vehicle'}
        >
          <form onSubmit={handleSaveVehicle} className="space-y-4">
            {vehicleFormError && <Alert type="error">{vehicleFormError}</Alert>}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Registration Number *
                </label>
                <Input
                  required
                  placeholder="e.g. TS09AB1234"
                  value={vehicleFormData.registration_number}
                  onChange={(e) =>
                    setVehicleFormData((prev) => ({ ...prev, registration_number: e.target.value.toUpperCase() }))
                  }
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Vehicle Code *
                </label>
                <Input
                  required
                  placeholder="e.g. BUS-01"
                  value={vehicleFormData.vehicle_code}
                  onChange={(e) =>
                    setVehicleFormData((prev) => ({ ...prev, vehicle_code: e.target.value.toUpperCase() }))
                  }
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Vehicle Type *
                </label>
                <select
                  value={vehicleFormData.vehicle_type}
                  onChange={(e) =>
                    setVehicleFormData((prev) => ({ ...prev, vehicle_type: e.target.value as VehicleType }))
                  }
                  className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
                >
                  <option value="BUS">Bus</option>
                  <option value="VAN">Van</option>
                  <option value="MINIBUS">Minibus</option>
                  <option value="AUTO">Auto</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Seating Capacity *
                </label>
                <Input
                  type="number"
                  min={1}
                  max={120}
                  required
                  value={vehicleFormData.seating_capacity}
                  onChange={(e) =>
                    setVehicleFormData((prev) => ({ ...prev, seating_capacity: Number(e.target.value) }))
                  }
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Fuel Type</label>
                <select
                  value={vehicleFormData.fuel_type || 'DIESEL'}
                  onChange={(e) =>
                    setVehicleFormData((prev) => ({ ...prev, fuel_type: e.target.value as FuelType }))
                  }
                  className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
                >
                  <option value="DIESEL">Diesel</option>
                  <option value="CNG">CNG</option>
                  <option value="PETROL">Petrol</option>
                  <option value="ELECTRIC">Electric</option>
                  <option value="HYBRID">Hybrid</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Status</label>
                <select
                  value={vehicleFormData.status}
                  onChange={(e) =>
                    setVehicleFormData((prev) => ({ ...prev, status: e.target.value as VehicleStatus }))
                  }
                  className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
                >
                  <option value="ACTIVE">Active</option>
                  <option value="MAINTENANCE">Maintenance</option>
                  <option value="DECOMMISSIONED">Decommissioned</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Insurance Expiry Date
                </label>
                <Input
                  type="date"
                  value={vehicleFormData.insurance_expiry_date || ''}
                  onChange={(e) => setVehicleFormData((prev) => ({ ...prev, insurance_expiry_date: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Fitness Expiry Date
                </label>
                <Input
                  type="date"
                  value={vehicleFormData.fitness_expiry_date || ''}
                  onChange={(e) => setVehicleFormData((prev) => ({ ...prev, fitness_expiry_date: e.target.value }))}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">GPS Device ID</label>
              <Input
                placeholder="Optional device identifier"
                value={vehicleFormData.gps_device_id || ''}
                onChange={(e) => setVehicleFormData((prev) => ({ ...prev, gps_device_id: e.target.value }))}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
              <Button type="button" variant="outline" onClick={() => setShowVehicleModal(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submittingVehicle}>
                {submittingVehicle ? 'Saving...' : editingVehicle ? 'Update Vehicle' : 'Create Vehicle'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* MODAL: CREATE / EDIT DRIVER                                          */}
      {/* -------------------------------------------------------------------- */}
      {showDriverModal && (
        <Modal
          isOpen={showDriverModal}
          onClose={() => setShowDriverModal(false)}
          title={editingDriver ? `Edit Driver: ${editingDriver.driver_name}` : 'Add Licensed Driver'}
        >
          <form onSubmit={handleSaveDriver} className="space-y-4">
            {driverFormError && <Alert type="error">{driverFormError}</Alert>}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Driver Full Name *
                </label>
                <Input
                  required
                  placeholder="e.g. Ramesh Kumar"
                  value={driverFormData.driver_name}
                  onChange={(e) => setDriverFormData((prev) => ({ ...prev, driver_name: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  License Number *
                </label>
                <Input
                  required
                  placeholder="e.g. DL-0420110012345"
                  value={driverFormData.license_number}
                  onChange={(e) =>
                    setDriverFormData((prev) => ({ ...prev, license_number: e.target.value.toUpperCase() }))
                  }
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Contact Phone *
                </label>
                <Input
                  required
                  placeholder="e.g. 9876543210"
                  value={driverFormData.contact_phone}
                  onChange={(e) => setDriverFormData((prev) => ({ ...prev, contact_phone: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  License Expiry Date
                </label>
                <Input
                  type="date"
                  value={driverFormData.license_expiry_date || ''}
                  onChange={(e) => setDriverFormData((prev) => ({ ...prev, license_expiry_date: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Emergency Phone
                </label>
                <Input
                  placeholder="e.g. 9876500000"
                  value={driverFormData.emergency_contact || ''}
                  onChange={(e) => setDriverFormData((prev) => ({ ...prev, emergency_contact: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Linked School Staff (Optional)
                </label>
                <select
                  value={driverFormData.staff_id || ''}
                  onChange={(e) => setDriverFormData((prev) => ({ ...prev, staff_id: e.target.value }))}
                  className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
                >
                  <option value="">No linked staff profile</option>
                  {teachersList.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.first_name} {t.last_name} ({t.employee_id})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Residential Address</label>
              <Input
                placeholder="Street address, city, pin code"
                value={driverFormData.address || ''}
                onChange={(e) => setDriverFormData((prev) => ({ ...prev, address: e.target.value }))}
              />
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="is_active"
                checked={driverFormData.is_active}
                onChange={(e) => setDriverFormData((prev) => ({ ...prev, is_active: e.target.checked }))}
                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              <label htmlFor="is_active" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                Driver is active and available for route assignment
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
              <Button type="button" variant="outline" onClick={() => setShowDriverModal(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submittingDriver}>
                {submittingDriver ? 'Saving...' : editingDriver ? 'Update Driver' : 'Create Driver'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* MODAL: CREATE / EDIT ROUTE                                           */}
      {/* -------------------------------------------------------------------- */}
      {showRouteModal && (
        <Modal
          isOpen={showRouteModal}
          onClose={() => setShowRouteModal(false)}
          title={editingRoute ? `Edit Route: ${editingRoute.route_code}` : 'Create Transit Route'}
        >
          <form onSubmit={handleSaveRoute} className="space-y-4">
            {routeFormError && <Alert type="error">{routeFormError}</Alert>}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Route Code *</label>
                <Input
                  required
                  placeholder="e.g. R-NORTH-1"
                  value={routeFormData.route_code}
                  onChange={(e) =>
                    setRouteFormData((prev) => ({ ...prev, route_code: e.target.value.toUpperCase() }))
                  }
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Route Name *</label>
                <Input
                  required
                  placeholder="e.g. North Campus Express"
                  value={routeFormData.route_name}
                  onChange={(e) => setRouteFormData((prev) => ({ ...prev, route_name: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Assigned Vehicle</label>
                <select
                  value={routeFormData.vehicle_id || ''}
                  onChange={(e) => setRouteFormData((prev) => ({ ...prev, vehicle_id: e.target.value }))}
                  className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
                >
                  <option value="">No Vehicle Assigned</option>
                  {vehicles.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.vehicle_code} - {v.registration_number} ({v.seating_capacity} seats)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Assigned Driver</label>
                <select
                  value={routeFormData.driver_id || ''}
                  onChange={(e) => setRouteFormData((prev) => ({ ...prev, driver_id: e.target.value }))}
                  className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
                >
                  <option value="">No Driver Assigned</option>
                  {drivers.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.driver_name} ({d.contact_phone})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Morning Start Time</label>
                <Input
                  type="time"
                  value={routeFormData.morning_start_time || '07:30'}
                  onChange={(e) => setRouteFormData((prev) => ({ ...prev, morning_start_time: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Evening Start Time</label>
                <Input
                  type="time"
                  value={routeFormData.evening_start_time || '15:30'}
                  onChange={(e) => setRouteFormData((prev) => ({ ...prev, evening_start_time: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Attendant Name</label>
                <Input
                  placeholder="Optional bus attendant"
                  value={routeFormData.attendant_name || ''}
                  onChange={(e) => setRouteFormData((prev) => ({ ...prev, attendant_name: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Attendant Phone</label>
                <Input
                  placeholder="e.g. 9876543210"
                  value={routeFormData.attendant_phone || ''}
                  onChange={(e) => setRouteFormData((prev) => ({ ...prev, attendant_phone: e.target.value }))}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Description</label>
              <Input
                placeholder="Route coverage description"
                value={routeFormData.description || ''}
                onChange={(e) => setRouteFormData((prev) => ({ ...prev, description: e.target.value }))}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
              <Button type="button" variant="outline" onClick={() => setShowRouteModal(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submittingRoute}>
                {submittingRoute ? 'Saving...' : editingRoute ? 'Update Route' : 'Create Route'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* MODAL: MANAGE ROUTE STOPS                                            */}
      {/* -------------------------------------------------------------------- */}
      {selectedRouteForStops && (
        <Modal
          isOpen={Boolean(selectedRouteForStops)}
          onClose={() => setSelectedRouteForStops(null)}
          title={`Route Stops: ${selectedRouteForStops.route_code} — ${selectedRouteForStops.route_name}`}
        >
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <p className="text-xs text-slate-500">
                Stops are sequenced in order of morning pickup and afternoon drop.
              </p>
              {canCreate && (
                <Button size="sm" onClick={handleOpenCreateStop} className="flex items-center gap-1 text-xs">
                  <Plus className="w-3.5 h-3.5" /> Add Stop
                </Button>
              )}
            </div>

            {loadingRouteStops && <LoadingState message="Loading stops..." />}
            {routeStopsError && <ErrorState message={routeStopsError} />}

            {!loadingRouteStops && !routeStopsError && routeStops.length === 0 && (
              <EmptyState
                icon={<MapPin className="w-8 h-8 text-slate-400" />}
                title="No Stops Defined"
                description="Add pickup and drop stops to this transit route."
              />
            )}

            {!loadingRouteStops && !routeStopsError && routeStops.length > 0 && (
              <div className="border border-slate-200 dark:border-slate-800 overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className="px-3 py-2 font-semibold w-12">Seq</th>
                      <th className="px-3 py-2 font-semibold">Stop Name</th>
                      <th className="px-3 py-2 font-semibold">Code</th>
                      <th className="px-3 py-2 font-semibold">Pickup Time</th>
                      <th className="px-3 py-2 font-semibold">Drop Time</th>
                      <th className="px-3 py-2 font-semibold">Fee</th>
                      <th className="px-3 py-2 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {routeStops.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="px-3 py-2 font-mono font-bold">{s.sequence_order}</td>
                        <td className="px-3 py-2 font-medium">{s.stop_name}</td>
                        <td className="px-3 py-2 font-mono">{s.stop_code}</td>
                        <td className="px-3 py-2 font-mono">{s.morning_pickup_time || '—'}</td>
                        <td className="px-3 py-2 font-mono">{s.afternoon_drop_time || '—'}</td>
                        <td className="px-3 py-2 font-mono">₹{s.pickup_fee_amount}</td>
                        <td className="px-3 py-2 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {canUpdate && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenEditStop(s)}
                                className="h-6 w-6 p-0"
                                title="Edit Stop"
                              >
                                <Edit2 className="w-3 h-3" />
                              </Button>
                            )}
                            {canDelete && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setDeletingStopId(s.id)}
                                className="h-6 w-6 p-0 text-red-600 hover:text-red-700"
                                title="Delete Stop"
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* MODAL: CREATE / EDIT STOP                                            */}
      {/* -------------------------------------------------------------------- */}
      {showStopModal && (
        <Modal
          isOpen={showStopModal}
          onClose={() => setShowStopModal(false)}
          title={editingStop ? `Edit Stop: ${editingStop.stop_name}` : 'Add Transit Stop'}
        >
          <form onSubmit={handleSaveStop} className="space-y-4">
            {stopFormError && <Alert type="error">{stopFormError}</Alert>}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Stop Name *</label>
                <Input
                  required
                  placeholder="e.g. Jubilee Hills Checkpost"
                  value={stopFormData.stop_name}
                  onChange={(e) => setStopFormData((prev) => ({ ...prev, stop_name: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Stop Code *</label>
                <Input
                  required
                  placeholder="e.g. ST-JH-01"
                  value={stopFormData.stop_code}
                  onChange={(e) =>
                    setStopFormData((prev) => ({ ...prev, stop_code: e.target.value.toUpperCase() }))
                  }
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Sequence Order *</label>
                <Input
                  type="number"
                  min={1}
                  required
                  value={stopFormData.sequence_order}
                  onChange={(e) => setStopFormData((prev) => ({ ...prev, sequence_order: Number(e.target.value) }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Pickup Fee (₹) *</label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={stopFormData.pickup_fee_amount}
                  onChange={(e) => setStopFormData((prev) => ({ ...prev, pickup_fee_amount: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Morning Pickup Time</label>
                <Input
                  type="time"
                  value={stopFormData.morning_pickup_time || '07:45'}
                  onChange={(e) => setStopFormData((prev) => ({ ...prev, morning_pickup_time: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Afternoon Drop Time</label>
                <Input
                  type="time"
                  value={stopFormData.afternoon_drop_time || '16:00'}
                  onChange={(e) => setStopFormData((prev) => ({ ...prev, afternoon_drop_time: e.target.value }))}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Landmark / Notes</label>
              <Input
                placeholder="Opposite Metro Pillar 124"
                value={stopFormData.landmark || ''}
                onChange={(e) => setStopFormData((prev) => ({ ...prev, landmark: e.target.value }))}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
              <Button type="button" variant="outline" onClick={() => setShowStopModal(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submittingStop}>
                {submittingStop ? 'Saving...' : editingStop ? 'Update Stop' : 'Add Stop'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* MODAL: CREATE STUDENT ALLOCATION                                     */}
      {/* -------------------------------------------------------------------- */}
      {showAllocationModal && (
        <Modal
          isOpen={showAllocationModal}
          onClose={() => setShowAllocationModal(false)}
          title="New Student Transport Allocation"
        >
          <form onSubmit={handleSaveAllocation} className="space-y-4">
            {allocationFormError && <Alert type="error">{allocationFormError}</Alert>}

            {/* Student Search */}
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Select Student *
              </label>
              <div className="space-y-1.5">
                <Input
                  placeholder="Type student name to search..."
                  onChange={(e) => searchStudents(e.target.value)}
                  className="text-xs"
                />
                {searchingStudents && <p className="text-[11px] text-slate-400">Searching directory...</p>}
                {studentOptions.length > 0 && (
                  <select
                    size={4}
                    value={allocationFormData.student_id}
                    onChange={(e) => setAllocationFormData((prev) => ({ ...prev, student_id: e.target.value }))}
                    className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs p-1"
                  >
                    {studentOptions.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.admission_number || 'No Adm No'})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            {/* Academic Year */}
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Academic Year *
              </label>
              <select
                required
                value={allocationFormData.academic_year_id}
                onChange={(e) => setAllocationFormData((prev) => ({ ...prev, academic_year_id: e.target.value }))}
                className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
              >
                {academicYears.map((ay) => (
                  <option key={ay.id} value={ay.id}>
                    {ay.name} {ay.status === 'ACTIVE' ? '(Active)' : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Route Selection */}
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Transit Route *</label>
              <select
                required
                value={allocationFormData.route_id}
                onChange={(e) => handleRouteChangeInAllocationForm(e.target.value)}
                className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
              >
                <option value="">-- Choose Route --</option>
                {routes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.route_code} — {r.route_name}
                  </option>
                ))}
              </select>
            </div>

            {/* Allocation Type */}
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Allocation Type *
              </label>
              <select
                value={allocationFormData.allocation_type}
                onChange={(e) =>
                  setAllocationFormData((prev) => ({
                    ...prev,
                    allocation_type: e.target.value as TransportAllocationType,
                  }))
                }
                className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
              >
                <option value="TWO_WAY">Two-Way (Pickup & Drop)</option>
                <option value="PICKUP_ONLY">Pickup Only (Morning)</option>
                <option value="DROP_ONLY">Drop Only (Afternoon)</option>
              </select>
            </div>

            {/* Cascading Route Stops Selection */}
            {allocationFormData.route_id && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800">
                {allocationFormData.allocation_type !== 'DROP_ONLY' && (
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Morning Pickup Stop *
                    </label>
                    <select
                      required
                      value={allocationFormData.pickup_stop_id || ''}
                      onChange={(e) => setAllocationFormData((prev) => ({ ...prev, pickup_stop_id: e.target.value }))}
                      className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
                    >
                      <option value="">-- Select Pickup Stop --</option>
                      {selectedRouteStopsForAllocation.map((s) => (
                        <option key={s.id} value={s.id}>
                          Seq {s.sequence_order}: {s.stop_name} ({s.morning_pickup_time || 'No Time'})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {allocationFormData.allocation_type !== 'PICKUP_ONLY' && (
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Afternoon Drop Stop *
                    </label>
                    <select
                      required
                      value={allocationFormData.drop_stop_id || ''}
                      onChange={(e) => setAllocationFormData((prev) => ({ ...prev, drop_stop_id: e.target.value }))}
                      className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
                    >
                      <option value="">-- Select Drop Stop --</option>
                      {selectedRouteStopsForAllocation.map((s) => (
                        <option key={s.id} value={s.id}>
                          Seq {s.sequence_order}: {s.stop_name} ({s.afternoon_drop_time || 'No Time'})
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Start Date *</label>
                <Input
                  type="date"
                  required
                  value={allocationFormData.start_date}
                  onChange={(e) => setAllocationFormData((prev) => ({ ...prev, start_date: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Remarks</label>
                <Input
                  placeholder="Optional notes"
                  value={allocationFormData.remarks || ''}
                  onChange={(e) => setAllocationFormData((prev) => ({ ...prev, remarks: e.target.value }))}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
              <Button type="button" variant="outline" onClick={() => setShowAllocationModal(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submittingAllocation}>
                {submittingAllocation ? 'Allocating...' : 'Create Allocation'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* MODAL: ALLOCATION STATUS TRANSITION                                  */}
      {/* -------------------------------------------------------------------- */}
      {statusTargetAllocation && (
        <Modal
          isOpen={Boolean(statusTargetAllocation)}
          onClose={() => setStatusTargetAllocation(null)}
          title={`Update Allocation Status: ${statusTargetAllocation.student_name || 'Student'}`}
        >
          <form onSubmit={handleSaveStatusChange} className="space-y-4">
            {statusChangeError && <Alert type="error">{statusChangeError}</Alert>}

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Target Status *</label>
              <select
                value={newAllocationStatus}
                onChange={(e) => setNewAllocationStatus(e.target.value as TransportAllocationStatus)}
                className="w-full border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs h-9 px-2.5"
              >
                <option value="ACTIVE">Active (Allocate / Re-activate Seat)</option>
                <option value="SUSPENDED">Suspended (Free Seat Temporarily)</option>
                <option value="CANCELLED">Cancelled (Permanently Discontinue)</option>
              </select>
            </div>

            {newAllocationStatus === 'CANCELLED' && (
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">End Date</label>
                <Input
                  type="date"
                  value={statusEndDate}
                  onChange={(e) => setStatusEndDate(e.target.value)}
                  placeholder="Defaults to today"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Reason / Remarks</label>
              <Input
                placeholder="Reason for status transition"
                value={statusRemarks}
                onChange={(e) => setStatusRemarks(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
              <Button type="button" variant="outline" onClick={() => setStatusTargetAllocation(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submittingStatusChange}>
                {submittingStatusChange ? 'Updating...' : 'Update Status'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* CONFIRM DIALOGS                                                      */}
      {/* -------------------------------------------------------------------- */}
      <ConfirmDialog
        isOpen={Boolean(deletingVehicleId)}
        title="Delete Vehicle"
        message="Are you sure you want to delete this vehicle from the fleet? This action will soft-delete the record."
        onConfirm={handleDeleteVehicle}
        onClose={() => setDeletingVehicleId(null)}
      />

      <ConfirmDialog
        isOpen={Boolean(deletingDriverId)}
        title="Delete Driver"
        message="Are you sure you want to delete this driver? Drivers assigned to active routes cannot be deleted."
        onConfirm={handleDeleteDriver}
        onClose={() => setDeletingDriverId(null)}
      />

      <ConfirmDialog
        isOpen={Boolean(deletingRouteId)}
        title="Delete Route"
        message="Are you sure you want to delete this route? Routes with active student passenger allocations cannot be deleted."
        onConfirm={handleDeleteRoute}
        onClose={() => setDeletingRouteId(null)}
      />

      <ConfirmDialog
        isOpen={Boolean(deletingStopId)}
        title="Delete Stop"
        message="Are you sure you want to delete this stop from the transit route?"
        onConfirm={handleDeleteStop}
        onClose={() => setDeletingStopId(null)}
      />

      <ConfirmDialog
        isOpen={Boolean(deletingAllocationId)}
        title="Delete Student Allocation"
        message="Are you sure you want to remove this student transport allocation?"
        onConfirm={handleDeleteAllocation}
        onClose={() => setDeletingAllocationId(null)}
      />
    </div>
  );
};
