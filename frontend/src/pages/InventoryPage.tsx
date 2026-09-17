import React, { useEffect, useState } from 'react';
import {
  Package,
  Layers,
  Boxes,
  ShieldCheck,
  UserCheck,
  MapPin,
  Truck,
  History,
  Search,
  Plus,
  Edit2,
  Trash2,
  ArrowRightLeft,
  ArrowDownLeft,
  ArrowUpRight,
  RotateCcw,
  Sliders,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Archive,
  RefreshCw,
  Eye,
  Building,
  GraduationCap,
  Users,
  Building2,
  Calendar,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { inventoryApi } from '@/services/api/inventoryApi';
import { teachersApi } from '@/services/api/teachersApi';
import { studentsApi } from '@/services/api/studentsApi';
import { classroomsApi } from '@/services/api/classroomsApi';
import { usersApi } from '@/services/api/usersApi';
import {
  AssetAssignment,
  AssetAssignmentCreate,
  AssetAssignmentReturnRequest,
  AssetAssignmentStatus,
  AssetAssignmentTransferRequest,
  AssetAssignmentType,
  AssetCondition,
  AssetStatus,
  Classroom,
  InventoryCategory,
  InventoryCategoryCreate,
  InventoryCategoryUpdate,
  InventoryItem,
  InventoryItemCreate,
  InventoryItemType,
  InventoryItemUpdate,
  InventoryLocation,
  InventoryLocationCreate,
  InventoryLocationType,
  InventoryLocationUpdate,
  InventoryStock,
  InventoryStockMovement,
  InventoryStockMovementType,
  InventoryStockSummary,
  InventoryVendor,
  InventoryVendorCreate,
  InventoryVendorUpdate,
  PhysicalAsset,
  PhysicalAssetCreate,
  PhysicalAssetRetireRequest,
  PhysicalAssetUpdate,
  StockAdjustmentRequest,
  StockIssueRequest,
  StockReceiveRequest,
  StockReturnRequest,
  StockTransferRequest,
  Student,
  Teacher,
  User,
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

export const InventoryPage: React.FC = () => {
  const { user, permissions, roles } = useAuthStore();
  const isSuperAdmin =
    user?.is_super_admin ||
    roles?.some((r: any) => r.name === 'Super Admin' || r.name === 'SUPER_ADMIN');

  const hasPermission = (perm: string) => isSuperAdmin || permissions.includes(perm);

  const canCreate = hasPermission('inventory.create');
  const canUpdate = hasPermission('inventory.update');
  const canDelete = hasPermission('inventory.delete');
  const canIssue = hasPermission('inventory.issue');
  const canTransfer = hasPermission('inventory.transfer');
  const canManage = hasPermission('inventory.manage');

  // Active Tab
  const [activeTab, setActiveTab] = useState<
    | 'dashboard'
    | 'catalog'
    | 'stock'
    | 'assets'
    | 'assignments'
    | 'locations'
    | 'vendors'
    | 'movements'
  >('dashboard');

  // Page Alert
  const [pageAlert, setPageAlert] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  // Common Reference Data
  const [categories, setCategories] = useState<InventoryCategory[]>([]);
  const [locations, setLocations] = useState<InventoryLocation[]>([]);
  const [vendors, setVendors] = useState<InventoryVendor[]>([]);
  const [allItemsList, setAllItemsList] = useState<InventoryItem[]>([]);
  const [teachersList, setTeachersList] = useState<Teacher[]>([]);
  const [studentsList, setStudentsList] = useState<Student[]>([]);
  const [classroomsList, setClassroomsList] = useState<Classroom[]>([]);
  const [usersList, setUsersList] = useState<User[]>([]);

  // ---------------------------------------------------------------------------
  // 1. Dashboard State
  // ---------------------------------------------------------------------------
  const [summary, setSummary] = useState<InventoryStockSummary | null>(null);
  const [lowStockList, setLowStockList] = useState<InventoryStock[]>([]);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // 2. Catalog (Items) State
  // ---------------------------------------------------------------------------
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [itemSearch, setItemSearch] = useState('');
  const [itemCategoryFilter, setItemCategoryFilter] = useState('');
  const [itemTypeFilter, setItemTypeFilter] = useState<string>('');
  const [itemPage, setItemPage] = useState(1);
  const [itemTotalPages, setItemTotalPages] = useState(1);
  const [loadingItems, setLoadingItems] = useState(false);
  const [itemError, setItemError] = useState<string | null>(null);

  const [showItemModal, setShowItemModal] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [itemFormData, setItemFormData] = useState<InventoryItemCreate>({
    category_id: '',
    item_code: '',
    name: '',
    description: '',
    item_type: 'CONSUMABLE',
    unit_of_measure: 'PCS',
    track_individually: false,
    reorder_level: 0,
    is_active: true,
  });
  const [deletingItemId, setDeletingItemId] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // 3. Stock Workstation State
  // ---------------------------------------------------------------------------
  const [stocks, setStocks] = useState<InventoryStock[]>([]);
  const [stockSearch, setStockSearch] = useState('');
  const [stockCategoryFilter, setStockCategoryFilter] = useState('');
  const [stockLocationFilter, setStockLocationFilter] = useState('');
  const [stockLowOnlyFilter, setStockLowOnlyFilter] = useState(false);
  const [stockPage, setStockPage] = useState(1);
  const [stockTotalPages, setStockTotalPages] = useState(1);
  const [loadingStock, setLoadingStock] = useState(false);
  const [stockError, setStockError] = useState<string | null>(null);

  // Stock Operations Modals
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [receiveForm, setReceiveForm] = useState<StockReceiveRequest>({
    item_id: '',
    location_id: '',
    quantity: 1,
    unit_price: undefined,
    vendor_id: undefined,
    reference_number: '',
    remarks: '',
  });

  const [showIssueModal, setShowIssueModal] = useState(false);
  const [issueForm, setIssueForm] = useState<StockIssueRequest>({
    item_id: '',
    location_id: '',
    quantity: 1,
    reference_number: '',
    remarks: '',
  });

  const [showReturnModal, setShowReturnModal] = useState(false);
  const [returnStockForm, setReturnStockForm] = useState<StockReturnRequest>({
    item_id: '',
    location_id: '',
    quantity: 1,
    reference_number: '',
    remarks: '',
  });

  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [adjustForm, setAdjustForm] = useState<StockAdjustmentRequest>({
    item_id: '',
    location_id: '',
    adjustment_type: 'ADD',
    quantity: 1,
    reason: '',
    reference_number: '',
  });

  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferStockForm, setTransferStockForm] = useState<StockTransferRequest>({
    item_id: '',
    source_location_id: '',
    destination_location_id: '',
    quantity: 1,
    reference_number: '',
    remarks: '',
  });

  // ---------------------------------------------------------------------------
  // 4. Physical Assets State
  // ---------------------------------------------------------------------------
  const [assets, setAssets] = useState<PhysicalAsset[]>([]);
  const [assetSearch, setAssetSearch] = useState('');
  const [assetStatusFilter, setAssetStatusFilter] = useState<string>('');
  const [assetConditionFilter, setAssetConditionFilter] = useState<string>('');
  const [assetLocationFilter, setAssetLocationFilter] = useState('');
  const [assetPage, setAssetPage] = useState(1);
  const [assetTotalPages, setAssetTotalPages] = useState(1);
  const [loadingAssets, setLoadingAssets] = useState(false);
  const [assetError, setAssetError] = useState<string | null>(null);

  const [showAssetModal, setShowAssetModal] = useState(false);
  const [editingAsset, setEditingAsset] = useState<PhysicalAsset | null>(null);
  const [assetFormData, setAssetFormData] = useState<PhysicalAssetCreate>({
    item_id: '',
    location_id: undefined,
    vendor_id: undefined,
    asset_tag: '',
    serial_number: '',
    model_number: '',
    status: 'AVAILABLE',
    condition: 'GOOD',
    purchase_date: '',
    purchase_cost: undefined,
    warranty_expiry_date: '',
    notes: '',
  });
  const [deletingAssetId, setDeletingAssetId] = useState<string | null>(null);

  const [showRetireModal, setShowRetireModal] = useState(false);
  const [retiringAssetId, setRetiringAssetId] = useState<string | null>(null);
  const [retireForm, setRetireForm] = useState<PhysicalAssetRetireRequest>({
    status: 'RETIRED',
    notes: '',
  });

  const [showAssetHistoryModal, setShowAssetHistoryModal] = useState(false);
  const [assetHistoryList, setAssetHistoryList] = useState<AssetAssignment[]>([]);
  const [selectedAssetForHistory, setSelectedAssetForHistory] = useState<PhysicalAsset | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // ---------------------------------------------------------------------------
  // 5. Asset Assignments State
  // ---------------------------------------------------------------------------
  const [assignments, setAssignments] = useState<AssetAssignment[]>([]);
  const [assignmentTypeFilter, setAssignmentTypeFilter] = useState<string>('');
  const [assignmentStatusFilter, setAssignmentStatusFilter] = useState<string>('');
  const [assignmentPage, setAssignmentPage] = useState(1);
  const [assignmentTotalPages, setAssignmentTotalPages] = useState(1);
  const [loadingAssignments, setLoadingAssignments] = useState(false);
  const [assignmentError, setAssignmentError] = useState<string | null>(null);

  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignFormData, setAssignFormData] = useState<AssetAssignmentCreate>({
    asset_id: '',
    assignment_type: 'STAFF',
    teacher_id: undefined,
    student_id: undefined,
    classroom_id: undefined,
    user_id: undefined,
    department_name: '',
    assigned_date: new Date().toISOString().split('T')[0],
    expected_return_date: '',
    condition_on_assignment: 'GOOD',
    remarks: '',
  });

  const [showReturnAssignmentModal, setShowReturnAssignmentModal] = useState(false);
  const [selectedAssignmentForReturn, setSelectedAssignmentForReturn] = useState<AssetAssignment | null>(null);
  const [returnAssignmentForm, setReturnAssignmentForm] = useState<AssetAssignmentReturnRequest>({
    actual_return_date: new Date().toISOString().split('T')[0],
    condition_on_return: 'GOOD',
    return_location_id: undefined,
    remarks: '',
  });

  const [showTransferAssignmentModal, setShowTransferAssignmentModal] = useState(false);
  const [selectedAssignmentForTransfer, setSelectedAssignmentForTransfer] = useState<AssetAssignment | null>(null);
  const [transferAssignmentForm, setTransferAssignmentForm] = useState<AssetAssignmentTransferRequest>({
    new_assignment_type: 'STAFF',
    new_teacher_id: undefined,
    new_student_id: undefined,
    new_classroom_id: undefined,
    new_user_id: undefined,
    new_department_name: '',
    transfer_date: new Date().toISOString().split('T')[0],
    condition: 'GOOD',
    remarks: '',
  });

  // ---------------------------------------------------------------------------
  // 6. Locations State
  // ---------------------------------------------------------------------------
  const [locationsList, setLocationsList] = useState<InventoryLocation[]>([]);
  const [locationSearch, setLocationSearch] = useState('');
  const [locationTypeFilter, setLocationTypeFilter] = useState<string>('');
  const [locationPage, setLocationPage] = useState(1);
  const [locationTotalPages, setLocationTotalPages] = useState(1);
  const [loadingLocations, setLoadingLocations] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);

  const [showLocationModal, setShowLocationModal] = useState(false);
  const [editingLocation, setEditingLocation] = useState<InventoryLocation | null>(null);
  const [locationFormData, setLocationFormData] = useState<InventoryLocationCreate>({
    name: '',
    code: '',
    location_type: 'STORE_ROOM',
    parent_location_id: undefined,
    building_name: '',
    description: '',
    is_active: true,
  });
  const [deletingLocationId, setDeletingLocationId] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // 7. Vendors State
  // ---------------------------------------------------------------------------
  const [vendorsList, setVendorsList] = useState<InventoryVendor[]>([]);
  const [vendorSearch, setVendorSearch] = useState('');
  const [vendorPage, setVendorPage] = useState(1);
  const [vendorTotalPages, setVendorTotalPages] = useState(1);
  const [loadingVendors, setLoadingVendors] = useState(false);
  const [vendorError, setVendorError] = useState<string | null>(null);

  const [showVendorModal, setShowVendorModal] = useState(false);
  const [editingVendor, setEditingVendor] = useState<InventoryVendor | null>(null);
  const [vendorFormData, setVendorFormData] = useState<InventoryVendorCreate>({
    name: '',
    code: '',
    contact_name: '',
    email: '',
    phone: '',
    address: '',
    tax_id: '',
    is_active: true,
  });
  const [deletingVendorId, setDeletingVendorId] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // 8. Movement History State
  // ---------------------------------------------------------------------------
  const [movements, setMovements] = useState<InventoryStockMovement[]>([]);
  const [movementTypeFilter, setMovementTypeFilter] = useState<string>('');
  const [movementItemFilter, setMovementItemFilter] = useState('');
  const [movementRefFilter, setMovementRefFilter] = useState('');
  const [movementPage, setMovementPage] = useState(1);
  const [movementTotalPages, setMovementTotalPages] = useState(1);
  const [loadingMovements, setLoadingMovements] = useState(false);
  const [movementError, setMovementError] = useState<string | null>(null);

  // Submitting states for operation safety
  const [isSubmitting, setIsSubmitting] = useState(false);

  // ---------------------------------------------------------------------------
  // Initial Data Fetching
  // ---------------------------------------------------------------------------
  useEffect(() => {
    loadCommonReferenceData();
  }, []);

  const loadCommonReferenceData = async () => {
    try {
      const [catRes, locRes, venRes, itmRes] = await Promise.all([
        inventoryApi.listCategories({ page_size: 100 }),
        inventoryApi.listLocations({ page_size: 100 }),
        inventoryApi.listVendors({ page_size: 100 }),
        inventoryApi.listItems({ page_size: 100 }),
      ]);
      setCategories(catRes.items);
      setLocations(locRes.items);
      setVendors(venRes.items);
      setAllItemsList(itmRes.items);
    } catch {
      // Non-fatal if ref data fails initially
    }

    try {
      const [tRes, sRes, cRes, uRes] = await Promise.all([
        teachersApi.getTeachers({ page_size: 100 }),
        studentsApi.getStudents({ page_size: 100 }),
        classroomsApi.getClassrooms({ page_size: 100 }),
        usersApi.getUsers({ page_size: 100 }),
      ]);
      setTeachersList(tRes.items || []);
      setStudentsList(sRes.items || []);
      setClassroomsList(cRes.items || []);
      setUsersList(uRes.items || []);
    } catch {
      // Ignored non-fatal target reference fetch
    }
  };

  // Tab change triggers
  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchDashboard();
    } else if (activeTab === 'catalog') {
      fetchItems();
    } else if (activeTab === 'stock') {
      fetchStock();
    } else if (activeTab === 'assets') {
      fetchAssets();
    } else if (activeTab === 'assignments') {
      fetchAssignments();
    } else if (activeTab === 'locations') {
      fetchLocations();
    } else if (activeTab === 'vendors') {
      fetchVendors();
    } else if (activeTab === 'movements') {
      fetchMovements();
    }
  }, [
    activeTab,
    itemPage,
    itemSearch,
    itemCategoryFilter,
    itemTypeFilter,
    stockPage,
    stockSearch,
    stockCategoryFilter,
    stockLocationFilter,
    stockLowOnlyFilter,
    assetPage,
    assetSearch,
    assetStatusFilter,
    assetConditionFilter,
    assetLocationFilter,
    assignmentPage,
    assignmentTypeFilter,
    assignmentStatusFilter,
    locationPage,
    locationSearch,
    locationTypeFilter,
    vendorPage,
    vendorSearch,
    movementPage,
    movementTypeFilter,
    movementItemFilter,
    movementRefFilter,
  ]);

  // ---------------------------------------------------------------------------
  // 1. Dashboard Handler
  // ---------------------------------------------------------------------------
  const fetchDashboard = async () => {
    setLoadingDashboard(true);
    setDashboardError(null);
    try {
      const [sumRes, lowRes] = await Promise.all([
        inventoryApi.getStockSummary(),
        inventoryApi.listStock({ low_stock: true, page_size: 10 }),
      ]);
      setSummary(sumRes);
      setLowStockList(lowRes.items);
    } catch (err: any) {
      setDashboardError(err.response?.data?.detail || 'Failed to load inventory summary.');
    } finally {
      setLoadingDashboard(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 2. Catalog Handlers
  // ---------------------------------------------------------------------------
  const fetchItems = async () => {
    setLoadingItems(true);
    setItemError(null);
    try {
      const res = await inventoryApi.listItems({
        search: itemSearch.trim() || undefined,
        category_id: itemCategoryFilter || undefined,
        item_type: (itemTypeFilter as InventoryItemType) || undefined,
        page: itemPage,
        page_size: 10,
      });
      setItems(res.items);
      setItemTotalPages(res.total_pages);
    } catch (err: any) {
      setItemError(err.response?.data?.detail || 'Failed to load item catalog.');
    } finally {
      setLoadingItems(false);
    }
  };

  const handleSaveItem = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      if (editingItem) {
        await inventoryApi.updateItem(editingItem.id, {
          category_id: itemFormData.category_id || undefined,
          item_code: itemFormData.item_code || undefined,
          name: itemFormData.name || undefined,
          description: itemFormData.description,
          item_type: itemFormData.item_type,
          unit_of_measure: itemFormData.unit_of_measure,
          track_individually: itemFormData.track_individually,
          reorder_level: Number(itemFormData.reorder_level) || 0,
          is_active: itemFormData.is_active,
        });
        setPageAlert({ type: 'success', message: 'Item updated successfully.' });
      } else {
        await inventoryApi.createItem({
          ...itemFormData,
          reorder_level: Number(itemFormData.reorder_level) || 0,
        });
        setPageAlert({ type: 'success', message: 'Item created successfully.' });
      }
      setShowItemModal(false);
      fetchItems();
      loadCommonReferenceData();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to save item.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteItem = async () => {
    if (!deletingItemId) return;
    setIsSubmitting(true);
    try {
      await inventoryApi.deleteItem(deletingItemId);
      setPageAlert({ type: 'success', message: 'Item removed successfully.' });
      setDeletingItemId(null);
      fetchItems();
      loadCommonReferenceData();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to delete item.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 3. Stock Handlers
  // ---------------------------------------------------------------------------
  const fetchStock = async () => {
    setLoadingStock(true);
    setStockError(null);
    try {
      const res = await inventoryApi.listStock({
        search: stockSearch.trim() || undefined,
        category_id: stockCategoryFilter || undefined,
        location_id: stockLocationFilter || undefined,
        low_stock: stockLowOnlyFilter ? true : undefined,
        page: stockPage,
        page_size: 10,
      });
      setStocks(res.items);
      setStockTotalPages(res.total_pages);
    } catch (err: any) {
      setStockError(err.response?.data?.detail || 'Failed to load stock levels.');
    } finally {
      setLoadingStock(false);
    }
  };

  const handleReceiveStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!receiveForm.item_id || !receiveForm.location_id || Number(receiveForm.quantity) <= 0) {
      setPageAlert({ type: 'error', message: 'Please select an item, location and positive quantity.' });
      return;
    }
    setIsSubmitting(true);
    try {
      await inventoryApi.receiveStock({
        ...receiveForm,
        quantity: Number(receiveForm.quantity),
        unit_price: receiveForm.unit_price ? Number(receiveForm.unit_price) : undefined,
        vendor_id: receiveForm.vendor_id || undefined,
      });
      setPageAlert({ type: 'success', message: 'Stock received successfully.' });
      setShowReceiveModal(false);
      fetchStock();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to receive stock.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleIssueStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!issueForm.item_id || !issueForm.location_id || Number(issueForm.quantity) <= 0) {
      setPageAlert({ type: 'error', message: 'Please select an item, location and positive quantity.' });
      return;
    }
    setIsSubmitting(true);
    try {
      await inventoryApi.issueStock({
        ...issueForm,
        quantity: Number(issueForm.quantity),
      });
      setPageAlert({ type: 'success', message: 'Stock issued successfully.' });
      setShowIssueModal(false);
      fetchStock();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to issue stock.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReturnStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!returnStockForm.item_id || !returnStockForm.location_id || Number(returnStockForm.quantity) <= 0) {
      setPageAlert({ type: 'error', message: 'Please select an item, location and positive quantity.' });
      return;
    }
    setIsSubmitting(true);
    try {
      await inventoryApi.returnStock({
        ...returnStockForm,
        quantity: Number(returnStockForm.quantity),
      });
      setPageAlert({ type: 'success', message: 'Stock returned successfully.' });
      setShowReturnModal(false);
      fetchStock();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to return stock.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAdjustStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adjustForm.item_id || !adjustForm.location_id || Number(adjustForm.quantity) <= 0 || !adjustForm.reason?.trim()) {
      setPageAlert({ type: 'error', message: 'Item, location, positive quantity and mandatory reason are required.' });
      return;
    }
    setIsSubmitting(true);
    try {
      await inventoryApi.adjustStock({
        ...adjustForm,
        quantity: Number(adjustForm.quantity),
      });
      setPageAlert({ type: 'success', message: 'Stock adjusted successfully.' });
      setShowAdjustModal(false);
      fetchStock();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to adjust stock.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTransferStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !transferStockForm.item_id ||
      !transferStockForm.source_location_id ||
      !transferStockForm.destination_location_id ||
      Number(transferStockForm.quantity) <= 0
    ) {
      setPageAlert({ type: 'error', message: 'Please specify item, source, destination and positive quantity.' });
      return;
    }
    if (transferStockForm.source_location_id === transferStockForm.destination_location_id) {
      setPageAlert({ type: 'error', message: 'Source and destination locations must be different.' });
      return;
    }
    setIsSubmitting(true);
    try {
      await inventoryApi.transferStock({
        ...transferStockForm,
        quantity: Number(transferStockForm.quantity),
      });
      setPageAlert({ type: 'success', message: 'Stock transferred successfully.' });
      setShowTransferModal(false);
      fetchStock();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to transfer stock.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 4. Physical Assets Handlers
  // ---------------------------------------------------------------------------
  const fetchAssets = async () => {
    setLoadingAssets(true);
    setAssetError(null);
    try {
      const res = await inventoryApi.listAssets({
        search: assetSearch.trim() || undefined,
        status: (assetStatusFilter as AssetStatus) || undefined,
        condition: (assetConditionFilter as AssetCondition) || undefined,
        location_id: assetLocationFilter || undefined,
        page: assetPage,
        page_size: 10,
      });
      setAssets(res.items);
      setAssetTotalPages(res.total_pages);
    } catch (err: any) {
      setAssetError(err.response?.data?.detail || 'Failed to load physical asset register.');
    } finally {
      setLoadingAssets(false);
    }
  };

  const handleSaveAsset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assetFormData.item_id || !assetFormData.asset_tag.trim()) {
      setPageAlert({ type: 'error', message: 'Item and Asset Tag are required.' });
      return;
    }
    setIsSubmitting(true);
    try {
      if (editingAsset) {
        await inventoryApi.updateAsset(editingAsset.id, {
          location_id: assetFormData.location_id || null,
          vendor_id: assetFormData.vendor_id || null,
          asset_tag: assetFormData.asset_tag,
          serial_number: assetFormData.serial_number || null,
          model_number: assetFormData.model_number || null,
          status: assetFormData.status,
          condition: assetFormData.condition,
          purchase_date: assetFormData.purchase_date || null,
          purchase_cost: assetFormData.purchase_cost ? Number(assetFormData.purchase_cost) : null,
          warranty_expiry_date: assetFormData.warranty_expiry_date || null,
          notes: assetFormData.notes || null,
        });
        setPageAlert({ type: 'success', message: 'Asset updated successfully.' });
      } else {
        await inventoryApi.createAsset({
          ...assetFormData,
          location_id: assetFormData.location_id || undefined,
          vendor_id: assetFormData.vendor_id || undefined,
          purchase_date: assetFormData.purchase_date || undefined,
          purchase_cost: assetFormData.purchase_cost ? Number(assetFormData.purchase_cost) : undefined,
          warranty_expiry_date: assetFormData.warranty_expiry_date || undefined,
        });
        setPageAlert({ type: 'success', message: 'Asset registered successfully.' });
      }
      setShowAssetModal(false);
      fetchAssets();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to save asset.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteAsset = async () => {
    if (!deletingAssetId) return;
    setIsSubmitting(true);
    try {
      await inventoryApi.deleteAsset(deletingAssetId);
      setPageAlert({ type: 'success', message: 'Asset deleted successfully.' });
      setDeletingAssetId(null);
      fetchAssets();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to delete asset.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetireAsset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!retiringAssetId) return;
    setIsSubmitting(true);
    try {
      await inventoryApi.retireAsset(retiringAssetId, retireForm);
      setPageAlert({ type: 'success', message: `Asset status set to ${retireForm.status}.` });
      setShowRetireModal(false);
      setRetiringAssetId(null);
      fetchAssets();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to retire asset.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewAssetHistory = async (asset: PhysicalAsset) => {
    setSelectedAssetForHistory(asset);
    setShowAssetHistoryModal(true);
    setLoadingHistory(true);
    try {
      const history = await inventoryApi.getAssetHistory(asset.id);
      setAssetHistoryList(history);
    } catch {
      setAssetHistoryList([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 5. Assignments Handlers
  // ---------------------------------------------------------------------------
  const fetchAssignments = async () => {
    setLoadingAssignments(true);
    setAssignmentError(null);
    try {
      const res = await inventoryApi.listAssignments({
        assignment_type: (assignmentTypeFilter as AssetAssignmentType) || undefined,
        status: (assignmentStatusFilter as AssetAssignmentStatus) || undefined,
        page: assignmentPage,
        page_size: 10,
      });
      setAssignments(res.items);
      setAssignmentTotalPages(res.total_pages);
    } catch (err: any) {
      setAssignmentError(err.response?.data?.detail || 'Failed to load asset assignments.');
    } finally {
      setLoadingAssignments(false);
    }
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignFormData.asset_id || !assignFormData.assigned_date) {
      setPageAlert({ type: 'error', message: 'Asset and Assigned Date are required.' });
      return;
    }
    // Validate target based on assignment type
    if (assignFormData.assignment_type === 'STAFF' && !assignFormData.teacher_id && !assignFormData.user_id) {
      setPageAlert({ type: 'error', message: 'Please select a Teacher or User for Staff assignment.' });
      return;
    }
    if (assignFormData.assignment_type === 'STUDENT' && !assignFormData.student_id) {
      setPageAlert({ type: 'error', message: 'Please select a Student.' });
      return;
    }
    if (assignFormData.assignment_type === 'CLASSROOM' && !assignFormData.classroom_id) {
      setPageAlert({ type: 'error', message: 'Please select a Classroom.' });
      return;
    }

    setIsSubmitting(true);
    try {
      await inventoryApi.assignAsset({
        ...assignFormData,
        teacher_id: assignFormData.teacher_id || undefined,
        student_id: assignFormData.student_id || undefined,
        classroom_id: assignFormData.classroom_id || undefined,
        user_id: assignFormData.user_id || undefined,
        department_name: assignFormData.department_name || undefined,
        expected_return_date: assignFormData.expected_return_date || undefined,
      });
      setPageAlert({ type: 'success', message: 'Asset assigned successfully.' });
      setShowAssignModal(false);
      fetchAssignments();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to assign asset.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReturnAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignmentForReturn) return;
    setIsSubmitting(true);
    try {
      await inventoryApi.returnAsset(selectedAssignmentForReturn.id, {
        ...returnAssignmentForm,
        return_location_id: returnAssignmentForm.return_location_id || undefined,
      });
      setPageAlert({ type: 'success', message: 'Asset returned successfully.' });
      setShowReturnAssignmentModal(false);
      setSelectedAssignmentForReturn(null);
      fetchAssignments();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to return asset.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTransferAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignmentForTransfer) return;
    setIsSubmitting(true);
    try {
      await inventoryApi.transferAssignment(selectedAssignmentForTransfer.id, {
        ...transferAssignmentForm,
        new_teacher_id: transferAssignmentForm.new_teacher_id || undefined,
        new_student_id: transferAssignmentForm.new_student_id || undefined,
        new_classroom_id: transferAssignmentForm.new_classroom_id || undefined,
        new_user_id: transferAssignmentForm.new_user_id || undefined,
        new_department_name: transferAssignmentForm.new_department_name || undefined,
      });
      setPageAlert({ type: 'success', message: 'Assignment transferred successfully.' });
      setShowTransferAssignmentModal(false);
      setSelectedAssignmentForTransfer(null);
      fetchAssignments();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to transfer assignment.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 6. Locations Handlers
  // ---------------------------------------------------------------------------
  const fetchLocations = async () => {
    setLoadingLocations(true);
    setLocationError(null);
    try {
      const res = await inventoryApi.listLocations({
        search: locationSearch.trim() || undefined,
        location_type: (locationTypeFilter as InventoryLocationType) || undefined,
        page: locationPage,
        page_size: 10,
      });
      setLocationsList(res.items);
      setLocationTotalPages(res.total_pages);
    } catch (err: any) {
      setLocationError(err.response?.data?.detail || 'Failed to load storage locations.');
    } finally {
      setLoadingLocations(false);
    }
  };

  const handleSaveLocation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!locationFormData.name.trim() || !locationFormData.code.trim()) {
      setPageAlert({ type: 'error', message: 'Name and Code are required.' });
      return;
    }
    setIsSubmitting(true);
    try {
      if (editingLocation) {
        await inventoryApi.updateLocation(editingLocation.id, {
          name: locationFormData.name,
          code: locationFormData.code,
          location_type: locationFormData.location_type,
          parent_location_id: locationFormData.parent_location_id || null,
          building_name: locationFormData.building_name || null,
          description: locationFormData.description || null,
          is_active: locationFormData.is_active,
        });
        setPageAlert({ type: 'success', message: 'Location updated successfully.' });
      } else {
        await inventoryApi.createLocation({
          ...locationFormData,
          parent_location_id: locationFormData.parent_location_id || undefined,
        });
        setPageAlert({ type: 'success', message: 'Location created successfully.' });
      }
      setShowLocationModal(false);
      fetchLocations();
      loadCommonReferenceData();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to save location.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteLocation = async () => {
    if (!deletingLocationId) return;
    setIsSubmitting(true);
    try {
      await inventoryApi.deleteLocation(deletingLocationId);
      setPageAlert({ type: 'success', message: 'Location deleted successfully.' });
      setDeletingLocationId(null);
      fetchLocations();
      loadCommonReferenceData();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to delete location.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 7. Vendors Handlers
  // ---------------------------------------------------------------------------
  const fetchVendors = async () => {
    setLoadingVendors(true);
    setVendorError(null);
    try {
      const res = await inventoryApi.listVendors({
        search: vendorSearch.trim() || undefined,
        page: vendorPage,
        page_size: 10,
      });
      setVendorsList(res.items);
      setVendorTotalPages(res.total_pages);
    } catch (err: any) {
      setVendorError(err.response?.data?.detail || 'Failed to load vendors.');
    } finally {
      setLoadingVendors(false);
    }
  };

  const handleSaveVendor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vendorFormData.name.trim() || !vendorFormData.code.trim()) {
      setPageAlert({ type: 'error', message: 'Vendor Name and Code are required.' });
      return;
    }
    setIsSubmitting(true);
    try {
      if (editingVendor) {
        await inventoryApi.updateVendor(editingVendor.id, {
          name: vendorFormData.name,
          code: vendorFormData.code,
          contact_name: vendorFormData.contact_name || null,
          email: vendorFormData.email || null,
          phone: vendorFormData.phone || null,
          address: vendorFormData.address || null,
          tax_id: vendorFormData.tax_id || null,
          is_active: vendorFormData.is_active,
        });
        setPageAlert({ type: 'success', message: 'Vendor updated successfully.' });
      } else {
        await inventoryApi.createVendor(vendorFormData);
        setPageAlert({ type: 'success', message: 'Vendor created successfully.' });
      }
      setShowVendorModal(false);
      fetchVendors();
      loadCommonReferenceData();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to save vendor.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteVendor = async () => {
    if (!deletingVendorId) return;
    setIsSubmitting(true);
    try {
      await inventoryApi.deleteVendor(deletingVendorId);
      setPageAlert({ type: 'success', message: 'Vendor removed successfully.' });
      setDeletingVendorId(null);
      fetchVendors();
      loadCommonReferenceData();
    } catch (err: any) {
      setPageAlert({ type: 'error', message: err.response?.data?.detail || 'Failed to delete vendor.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 8. Movements Handlers
  // ---------------------------------------------------------------------------
  const fetchMovements = async () => {
    setLoadingMovements(true);
    setMovementError(null);
    try {
      const res = await inventoryApi.listMovements({
        movement_type: (movementTypeFilter as InventoryStockMovementType) || undefined,
        item_id: movementItemFilter || undefined,
        reference_number: movementRefFilter.trim() || undefined,
        page: movementPage,
        page_size: 10,
      });
      setMovements(res.items);
      setMovementTotalPages(res.total_pages);
    } catch (err: any) {
      setMovementError(err.response?.data?.detail || 'Failed to load stock movements.');
    } finally {
      setLoadingMovements(false);
    }
  };

  // Helpers
  const getStatusBadge = (status: AssetStatus) => {
    switch (status) {
      case 'AVAILABLE':
        return <Badge variant="success">Available</Badge>;
      case 'ASSIGNED':
        return <Badge variant="info">Assigned</Badge>;
      case 'IN_REPAIR':
        return <Badge variant="warning">In Repair</Badge>;
      case 'DAMAGED':
        return <Badge variant="error">Damaged</Badge>;
      case 'LOST':
        return <Badge variant="error">Lost</Badge>;
      case 'RETIRED':
        return <Badge variant="neutral">Retired</Badge>;
      case 'DISPOSED':
        return <Badge variant="neutral">Disposed</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getConditionBadge = (condition: AssetCondition) => {
    switch (condition) {
      case 'EXCELLENT':
        return <Badge variant="success">Excellent</Badge>;
      case 'GOOD':
        return <Badge variant="info">Good</Badge>;
      case 'FAIR':
        return <Badge variant="warning">Fair</Badge>;
      case 'POOR':
        return <Badge variant="error">Poor</Badge>;
      case 'DAMAGED':
        return <Badge variant="error">Damaged</Badge>;
      default:
        return <Badge variant="neutral">{condition}</Badge>;
    }
  };

  const getMovementBadge = (type: InventoryStockMovementType) => {
    switch (type) {
      case 'PURCHASE_RECEIPT':
        return <Badge variant="success">Receipt</Badge>;
      case 'ISSUE':
        return <Badge variant="warning">Issue</Badge>;
      case 'TRANSFER':
        return <Badge variant="info">Transfer</Badge>;
      case 'RETURN':
        return <Badge variant="neutral">Return</Badge>;
      case 'ADJUSTMENT':
        return <Badge variant="error">Adjustment</Badge>;
      case 'DISCARD':
        return <Badge variant="error">Discard</Badge>;
      default:
        return <Badge variant="neutral">{type}</Badge>;
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-divider pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink flex items-center gap-2.5">
            <Package className="w-7 h-7 text-brand-500" />
            Inventory & Asset Management
          </h1>
          <p className="text-xs text-ink-muted mt-1">
            Centralized operational workstation for school stock, assets, custodianship, and supply logistics.
          </p>
        </div>
      </div>

      {/* Global Alert */}
      {pageAlert && (
        <Alert
          type={pageAlert.type === 'success' ? 'success' : 'error'}
          onClose={() => setPageAlert(null)}
        >
          {pageAlert.message}
        </Alert>
      )}

      {/* Workstation Tabs */}
      <div className="flex border-b border-divider gap-1 overflow-x-auto">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'dashboard'
              ? 'border-brand-500 text-brand-500 dark:text-brand-300'
              : 'border-transparent text-ink-muted hover:text-ink'
          }`}
        >
          <Layers className="w-4 h-4" />
          Overview
        </button>

        <button
          onClick={() => setActiveTab('catalog')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'catalog'
              ? 'border-brand-500 text-brand-500 dark:text-brand-300'
              : 'border-transparent text-ink-muted hover:text-ink'
          }`}
        >
          <Boxes className="w-4 h-4" />
          Item Catalog
        </button>

        <button
          onClick={() => setActiveTab('stock')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'stock'
              ? 'border-brand-500 text-brand-500 dark:text-brand-300'
              : 'border-transparent text-ink-muted hover:text-ink'
          }`}
        >
          <Package className="w-4 h-4" />
          Stock Levels
        </button>

        <button
          onClick={() => setActiveTab('assets')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'assets'
              ? 'border-brand-500 text-brand-500 dark:text-brand-300'
              : 'border-transparent text-ink-muted hover:text-ink'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Physical Assets
        </button>

        <button
          onClick={() => setActiveTab('assignments')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'assignments'
              ? 'border-brand-500 text-brand-500 dark:text-brand-300'
              : 'border-transparent text-ink-muted hover:text-ink'
          }`}
        >
          <UserCheck className="w-4 h-4" />
          Assignments
        </button>

        <button
          onClick={() => setActiveTab('locations')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'locations'
              ? 'border-brand-500 text-brand-500 dark:text-brand-300'
              : 'border-transparent text-ink-muted hover:text-ink'
          }`}
        >
          <MapPin className="w-4 h-4" />
          Locations
        </button>

        <button
          onClick={() => setActiveTab('vendors')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'vendors'
              ? 'border-brand-500 text-brand-500 dark:text-brand-300'
              : 'border-transparent text-ink-muted hover:text-ink'
          }`}
        >
          <Truck className="w-4 h-4" />
          Vendors
        </button>

        <button
          onClick={() => setActiveTab('movements')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'movements'
              ? 'border-brand-500 text-brand-500 dark:text-brand-300'
              : 'border-transparent text-ink-muted hover:text-ink'
          }`}
        >
          <History className="w-4 h-4" />
          Movement History
        </button>
      </div>

      {/* ===================================================================== */}
      {/* 1. OVERVIEW DASHBOARD */}
      {/* ===================================================================== */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {loadingDashboard && <LoadingState message="Loading inventory KPIs..." />}
          {dashboardError && <ErrorState message={dashboardError} onRetry={fetchDashboard} />}

          {!loadingDashboard && summary && (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                <Card>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-ink-muted">Catalog Items</p>
                      <h3 className="text-2xl font-bold mt-1 text-ink">{summary.total_items}</h3>
                    </div>
                    <div className="p-2.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 rounded-lg">
                      <Boxes className="w-5 h-5" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-ink-muted">Total Units in Stock</p>
                      <h3 className="text-2xl font-bold mt-1 text-ink">{summary.total_stock_units}</h3>
                    </div>
                    <div className="p-2.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 rounded-lg">
                      <Package className="w-5 h-5" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-ink-muted">Storage Locations</p>
                      <h3 className="text-2xl font-bold mt-1 text-ink">{summary.total_locations}</h3>
                    </div>
                    <div className="p-2.5 bg-purple-50 dark:bg-purple-900/20 text-purple-600 rounded-lg">
                      <MapPin className="w-5 h-5" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-ink-muted">Low Stock Items</p>
                      <h3 className="text-2xl font-bold mt-1 text-amber-600">{summary.low_stock_items_count}</h3>
                    </div>
                    <div className="p-2.5 bg-amber-50 dark:bg-amber-900/20 text-amber-600 rounded-lg">
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-ink-muted">Out of Stock</p>
                      <h3 className="text-2xl font-bold mt-1 text-rose-600">{summary.out_of_stock_items_count}</h3>
                    </div>
                    <div className="p-2.5 bg-rose-50 dark:bg-rose-900/20 text-rose-600 rounded-lg">
                      <XCircle className="w-5 h-5" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Low Stock Alerts & Quick Actions */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card className="lg:col-span-2">
                  <CardHeader className="pb-3 border-b border-divider flex flex-row items-center justify-between">
                    <CardTitle className="text-sm font-semibold flex items-center gap-2 text-amber-600">
                      <AlertTriangle className="w-4 h-4" />
                      Low Stock Alerts
                    </CardTitle>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setStockLowOnlyFilter(true);
                        setActiveTab('stock');
                      }}
                    >
                      View All in Stock View
                    </Button>
                  </CardHeader>
                  <CardContent className="p-0">
                    {lowStockList.length === 0 ? (
                      <div className="p-6 text-center text-xs text-ink-muted">
                        All items are currently at or above healthy reorder thresholds.
                      </div>
                    ) : (
                      <div className="divide-y divide-divider">
                        {lowStockList.map((stk) => (
                          <div key={stk.id} className="p-4 flex items-center justify-between text-xs">
                            <div>
                              <p className="font-semibold text-ink">{stk.item?.name}</p>
                              <p className="text-ink-muted text-[11px] mt-0.5">
                                Code: {stk.item?.item_code} · Location: {stk.location?.name || 'N/A'}
                              </p>
                            </div>
                            <div className="text-right">
                              <span className="font-mono font-bold text-amber-600">
                                {stk.quantity} {stk.item?.unit_of_measure}
                              </span>
                              <p className="text-[10px] text-ink-muted">
                                Reorder at: {stk.item?.reorder_level}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3 border-b border-divider">
                    <CardTitle className="text-sm font-semibold">Quick Operations</CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 space-y-2.5">
                    {canCreate && (
                      <Button
                        className="w-full justify-start text-xs"
                        onClick={() => {
                          setReceiveForm({
                            item_id: '',
                            location_id: '',
                            quantity: 1,
                            unit_price: undefined,
                            vendor_id: undefined,
                            reference_number: '',
                            remarks: '',
                          });
                          setShowReceiveModal(true);
                        }}
                      >
                        <ArrowDownLeft className="w-4 h-4 mr-2" />
                        Receive Stock (Purchase)
                      </Button>
                    )}

                    {canIssue && (
                      <Button
                        variant="outline"
                        className="w-full justify-start text-xs"
                        onClick={() => {
                          setIssueForm({
                            item_id: '',
                            location_id: '',
                            quantity: 1,
                            reference_number: '',
                            remarks: '',
                          });
                          setShowIssueModal(true);
                        }}
                      >
                        <ArrowUpRight className="w-4 h-4 mr-2" />
                        Issue Consumables
                      </Button>
                    )}

                    {canIssue && (
                      <Button
                        variant="outline"
                        className="w-full justify-start text-xs"
                        onClick={() => {
                          setAssignFormData({
                            asset_id: '',
                            assignment_type: 'STAFF',
                            assigned_date: new Date().toISOString().split('T')[0],
                            condition_on_assignment: 'GOOD',
                            remarks: '',
                          });
                          setShowAssignModal(true);
                        }}
                      >
                        <UserCheck className="w-4 h-4 mr-2" />
                        Assign Asset to Custodian
                      </Button>
                    )}

                    <Button
                      variant="outline"
                      className="w-full justify-start text-xs"
                      onClick={() => setActiveTab('movements')}
                    >
                      <History className="w-4 h-4 mr-2" />
                      View Audit Log
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* 2. ITEM CATALOG */}
      {/* ===================================================================== */}
      {activeTab === 'catalog' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2.5 flex-1">
              <div className="relative w-64">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-ink-muted" />
                <Input
                  placeholder="Search item name or code..."
                  value={itemSearch}
                  onChange={(e) => {
                    setItemSearch(e.target.value);
                    setItemPage(1);
                  }}
                  className="pl-9 text-xs"
                />
              </div>

              <select
                value={itemCategoryFilter}
                onChange={(e) => {
                  setItemCategoryFilter(e.target.value);
                  setItemPage(1);
                }}
                className="px-3 py-1.5 text-xs bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">All Categories</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>

              <select
                value={itemTypeFilter}
                onChange={(e) => {
                  setItemTypeFilter(e.target.value);
                  setItemPage(1);
                }}
                className="px-3 py-1.5 text-xs bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">All Types</option>
                <option value="CONSUMABLE">Consumables</option>
                <option value="ASSET">Physical Assets</option>
              </select>
            </div>

            {canCreate && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingItem(null);
                  setItemFormData({
                    category_id: categories[0]?.id || '',
                    item_code: '',
                    name: '',
                    description: '',
                    item_type: 'CONSUMABLE',
                    unit_of_measure: 'PCS',
                    track_individually: false,
                    reorder_level: 0,
                    is_active: true,
                  });
                  setShowItemModal(true);
                }}
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Add Item
              </Button>
            )}
          </div>

          <Card>
            <CardContent className="p-0">
              {loadingItems && <LoadingState message="Loading catalog items..." />}
              {itemError && <ErrorState message={itemError} onRetry={fetchItems} />}

              {!loadingItems && !itemError && items.length === 0 && (
                <EmptyState
                  title="No items found"
                  description="Add items to your catalog to track inventory quantities and physical assets."
                />
              )}

              {!loadingItems && !itemError && items.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-paper-dim border-b border-divider text-ink-muted uppercase font-mono text-[10px]">
                      <tr>
                        <th className="px-4 py-3">Code</th>
                        <th className="px-4 py-3">Name</th>
                        <th className="px-4 py-3">Category</th>
                        <th className="px-4 py-3">Type</th>
                        <th className="px-4 py-3">Unit</th>
                        <th className="px-4 py-3">Reorder Threshold</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-divider">
                      {items.map((it) => (
                        <tr key={it.id} className="hover:bg-paper-hover">
                          <td className="px-4 py-3 font-mono font-medium text-ink">{it.item_code}</td>
                          <td className="px-4 py-3 font-medium text-ink">{it.name}</td>
                          <td className="px-4 py-3 text-ink-muted">{it.category?.name || 'N/A'}</td>
                          <td className="px-4 py-3">
                            <Badge variant={it.item_type === 'ASSET' ? 'info' : 'neutral'}>
                              {it.item_type}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-ink-muted">{it.unit_of_measure}</td>
                          <td className="px-4 py-3 font-mono text-ink-muted">{it.reorder_level}</td>
                          <td className="px-4 py-3">
                            <Badge variant={it.is_active ? 'success' : 'neutral'}>
                              {it.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-right space-x-1.5">
                            {canUpdate && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setEditingItem(it);
                                  setItemFormData({
                                    category_id: it.category_id,
                                    item_code: it.item_code,
                                    name: it.name,
                                    description: it.description || '',
                                    item_type: it.item_type,
                                    unit_of_measure: it.unit_of_measure,
                                    track_individually: it.track_individually,
                                    reorder_level: it.reorder_level,
                                    is_active: it.is_active,
                                  });
                                  setShowItemModal(true);
                                }}
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </Button>
                            )}
                            {canDelete && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-rose-600 hover:text-rose-700"
                                onClick={() => setDeletingItemId(it.id)}
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {itemTotalPages > 1 && (
            <Pagination page={itemPage} totalPages={itemTotalPages} onPageChange={setItemPage} />
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* 3. STOCK WORKSTATION */}
      {/* ===================================================================== */}
      {activeTab === 'stock' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2.5 flex-1">
              <div className="relative w-64">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-ink-muted" />
                <Input
                  placeholder="Search item or code..."
                  value={stockSearch}
                  onChange={(e) => {
                    setStockSearch(e.target.value);
                    setStockPage(1);
                  }}
                  className="pl-9 text-xs"
                />
              </div>

              <select
                value={stockLocationFilter}
                onChange={(e) => {
                  setStockLocationFilter(e.target.value);
                  setStockPage(1);
                }}
                className="px-3 py-1.5 text-xs bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">All Locations</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name} ({loc.code})
                  </option>
                ))}
              </select>

              <select
                value={stockCategoryFilter}
                onChange={(e) => {
                  setStockCategoryFilter(e.target.value);
                  setStockPage(1);
                }}
                className="px-3 py-1.5 text-xs bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">All Categories</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>

              <label className="flex items-center gap-1.5 text-xs text-ink select-none cursor-pointer">
                <input
                  type="checkbox"
                  checked={stockLowOnlyFilter}
                  onChange={(e) => {
                    setStockLowOnlyFilter(e.target.checked);
                    setStockPage(1);
                  }}
                  className="rounded border-divider"
                />
                Low Stock Only
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {canCreate && (
                <Button
                  size="sm"
                  onClick={() => {
                    setReceiveForm({
                      item_id: allItemsList[0]?.id || '',
                      location_id: locations[0]?.id || '',
                      quantity: 1,
                      unit_price: undefined,
                      vendor_id: undefined,
                      reference_number: '',
                      remarks: '',
                    });
                    setShowReceiveModal(true);
                  }}
                >
                  <ArrowDownLeft className="w-4 h-4 mr-1.5" />
                  Receive
                </Button>
              )}

              {canIssue && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setIssueForm({
                      item_id: allItemsList[0]?.id || '',
                      location_id: locations[0]?.id || '',
                      quantity: 1,
                      reference_number: '',
                      remarks: '',
                    });
                    setShowIssueModal(true);
                  }}
                >
                  <ArrowUpRight className="w-4 h-4 mr-1.5" />
                  Issue
                </Button>
              )}

              {canIssue && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setReturnStockForm({
                      item_id: allItemsList[0]?.id || '',
                      location_id: locations[0]?.id || '',
                      quantity: 1,
                      reference_number: '',
                      remarks: '',
                    });
                    setShowReturnModal(true);
                  }}
                >
                  <RotateCcw className="w-4 h-4 mr-1.5" />
                  Return
                </Button>
              )}

              {canManage && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setAdjustForm({
                      item_id: allItemsList[0]?.id || '',
                      location_id: locations[0]?.id || '',
                      adjustment_type: 'ADD',
                      quantity: 1,
                      reason: '',
                      reference_number: '',
                    });
                    setShowAdjustModal(true);
                  }}
                >
                  <Sliders className="w-4 h-4 mr-1.5" />
                  Adjust
                </Button>
              )}

              {canTransfer && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setTransferStockForm({
                      item_id: allItemsList[0]?.id || '',
                      source_location_id: locations[0]?.id || '',
                      destination_location_id: locations[1]?.id || '',
                      quantity: 1,
                      reference_number: '',
                      remarks: '',
                    });
                    setShowTransferModal(true);
                  }}
                >
                  <ArrowRightLeft className="w-4 h-4 mr-1.5" />
                  Transfer
                </Button>
              )}
            </div>
          </div>

          <Card>
            <CardContent className="p-0">
              {loadingStock && <LoadingState message="Loading location stock balances..." />}
              {stockError && <ErrorState message={stockError} onRetry={fetchStock} />}

              {!loadingStock && !stockError && stocks.length === 0 && (
                <EmptyState
                  title="No stock records found"
                  description="Use the Receive button to add stock balances into storage locations."
                />
              )}

              {!loadingStock && !stockError && stocks.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-paper-dim border-b border-divider text-ink-muted uppercase font-mono text-[10px]">
                      <tr>
                        <th className="px-4 py-3">Item</th>
                        <th className="px-4 py-3">Location</th>
                        <th className="px-4 py-3">Available Quantity</th>
                        <th className="px-4 py-3">Reserved</th>
                        <th className="px-4 py-3">Unit Price</th>
                        <th className="px-4 py-3">Health Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-divider">
                      {stocks.map((stk) => {
                        const isLow = (stk.item?.reorder_level || 0) > 0 && stk.quantity <= (stk.item?.reorder_level || 0);
                        const isOut = stk.quantity === 0;

                        return (
                          <tr key={stk.id} className="hover:bg-paper-hover">
                            <td className="px-4 py-3 font-medium text-ink">
                              <div>{stk.item?.name}</div>
                              <div className="text-[10px] font-mono text-ink-muted">{stk.item?.item_code}</div>
                            </td>
                            <td className="px-4 py-3 text-ink-muted">
                              <div>{stk.location?.name}</div>
                              <div className="text-[10px] text-ink-muted/70">{stk.location?.code}</div>
                            </td>
                            <td className="px-4 py-3 font-mono font-semibold text-ink">
                              {stk.quantity} {stk.item?.unit_of_measure}
                            </td>
                            <td className="px-4 py-3 font-mono text-ink-muted">{stk.reserved_quantity}</td>
                            <td className="px-4 py-3 font-mono text-ink-muted">
                              {stk.unit_price != null ? `$${Number(stk.unit_price).toFixed(2)}` : '—'}
                            </td>
                            <td className="px-4 py-3">
                              {isOut ? (
                                <Badge variant="error">Out of Stock</Badge>
                              ) : isLow ? (
                                <Badge variant="warning">Low Stock</Badge>
                              ) : (
                                <Badge variant="success">Healthy</Badge>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {stockTotalPages > 1 && (
            <Pagination page={stockPage} totalPages={stockTotalPages} onPageChange={setStockPage} />
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* 4. PHYSICAL ASSETS */}
      {/* ===================================================================== */}
      {activeTab === 'assets' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2.5 flex-1">
              <div className="relative w-64">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-ink-muted" />
                <Input
                  placeholder="Search tag, serial, model..."
                  value={assetSearch}
                  onChange={(e) => {
                    setAssetSearch(e.target.value);
                    setAssetPage(1);
                  }}
                  className="pl-9 text-xs"
                />
              </div>

              <select
                value={assetStatusFilter}
                onChange={(e) => {
                  setAssetStatusFilter(e.target.value);
                  setAssetPage(1);
                }}
                className="px-3 py-1.5 text-xs bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">All Statuses</option>
                <option value="AVAILABLE">Available</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="IN_REPAIR">In Repair</option>
                <option value="DAMAGED">Damaged</option>
                <option value="LOST">Lost</option>
                <option value="RETIRED">Retired</option>
                <option value="DISPOSED">Disposed</option>
              </select>

              <select
                value={assetConditionFilter}
                onChange={(e) => {
                  setAssetConditionFilter(e.target.value);
                  setAssetPage(1);
                }}
                className="px-3 py-1.5 text-xs bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">All Conditions</option>
                <option value="EXCELLENT">Excellent</option>
                <option value="GOOD">Good</option>
                <option value="FAIR">Fair</option>
                <option value="POOR">Poor</option>
                <option value="DAMAGED">Damaged</option>
              </select>
            </div>

            {canCreate && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingAsset(null);
                  setAssetFormData({
                    item_id: allItemsList.find((i) => i.item_type === 'ASSET')?.id || allItemsList[0]?.id || '',
                    location_id: locations[0]?.id || undefined,
                    vendor_id: undefined,
                    asset_tag: '',
                    serial_number: '',
                    model_number: '',
                    status: 'AVAILABLE',
                    condition: 'GOOD',
                    purchase_date: '',
                    purchase_cost: undefined,
                    warranty_expiry_date: '',
                    notes: '',
                  });
                  setShowAssetModal(true);
                }}
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Register Asset
              </Button>
            )}
          </div>

          <Card>
            <CardContent className="p-0">
              {loadingAssets && <LoadingState message="Loading physical assets..." />}
              {assetError && <ErrorState message={assetError} onRetry={fetchAssets} />}

              {!loadingAssets && !assetError && assets.length === 0 && (
                <EmptyState
                  title="No assets found"
                  description="Register physical items with unique asset tags and serial numbers."
                />
              )}

              {!loadingAssets && !assetError && assets.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-paper-dim border-b border-divider text-ink-muted uppercase font-mono text-[10px]">
                      <tr>
                        <th className="px-4 py-3">Asset Tag</th>
                        <th className="px-4 py-3">Item / Description</th>
                        <th className="px-4 py-3">Serial / Model</th>
                        <th className="px-4 py-3">Location</th>
                        <th className="px-4 py-3">Condition</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-divider">
                      {assets.map((ast) => (
                        <tr key={ast.id} className="hover:bg-paper-hover">
                          <td className="px-4 py-3 font-mono font-bold text-brand-600 dark:text-brand-400">
                            {ast.asset_tag}
                          </td>
                          <td className="px-4 py-3 font-medium text-ink">
                            <div>{ast.item?.name}</div>
                            <div className="text-[10px] text-ink-muted">{ast.item?.item_code}</div>
                          </td>
                          <td className="px-4 py-3 text-ink-muted">
                            <div>SN: {ast.serial_number || '—'}</div>
                            <div className="text-[10px]">Model: {ast.model_number || '—'}</div>
                          </td>
                          <td className="px-4 py-3 text-ink-muted">{ast.location?.name || 'Unassigned'}</td>
                          <td className="px-4 py-3">{getConditionBadge(ast.condition)}</td>
                          <td className="px-4 py-3">{getStatusBadge(ast.status)}</td>
                          <td className="px-4 py-3 text-right space-x-1.5">
                            <Button
                              variant="ghost"
                              size="sm"
                              title="View History"
                              onClick={() => handleViewAssetHistory(ast)}
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </Button>

                            {canUpdate && (
                              <Button
                                variant="ghost"
                                size="sm"
                                title="Edit Asset"
                                onClick={() => {
                                  setEditingAsset(ast);
                                  setAssetFormData({
                                    item_id: ast.item_id,
                                    location_id: ast.location_id || undefined,
                                    vendor_id: ast.vendor_id || undefined,
                                    asset_tag: ast.asset_tag,
                                    serial_number: ast.serial_number || '',
                                    model_number: ast.model_number || '',
                                    status: ast.status,
                                    condition: ast.condition,
                                    purchase_date: ast.purchase_date || '',
                                    purchase_cost: ast.purchase_cost ? Number(ast.purchase_cost) : undefined,
                                    warranty_expiry_date: ast.warranty_expiry_date || '',
                                    notes: ast.notes || '',
                                  });
                                  setShowAssetModal(true);
                                }}
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </Button>
                            )}

                            {canManage && ast.status !== 'RETIRED' && ast.status !== 'DISPOSED' && (
                              <Button
                                variant="ghost"
                                size="sm"
                                title="Retire/Dispose Asset"
                                onClick={() => {
                                  setRetiringAssetId(ast.id);
                                  setRetireForm({ status: 'RETIRED', notes: '' });
                                  setShowRetireModal(true);
                                }}
                              >
                                <Archive className="w-3.5 h-3.5" />
                              </Button>
                            )}

                            {canDelete && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-rose-600 hover:text-rose-700"
                                onClick={() => setDeletingAssetId(ast.id)}
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {assetTotalPages > 1 && (
            <Pagination page={assetPage} totalPages={assetTotalPages} onPageChange={setAssetPage} />
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* 5. ASSET ASSIGNMENTS */}
      {/* ===================================================================== */}
      {activeTab === 'assignments' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2.5 flex-1">
              <select
                value={assignmentTypeFilter}
                onChange={(e) => {
                  setAssignmentTypeFilter(e.target.value);
                  setAssignmentPage(1);
                }}
                className="px-3 py-1.5 text-xs bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">All Assignment Types</option>
                <option value="STAFF">Teacher / Staff</option>
                <option value="STUDENT">Student</option>
                <option value="CLASSROOM">Classroom</option>
                <option value="DEPARTMENT">Department</option>
              </select>

              <select
                value={assignmentStatusFilter}
                onChange={(e) => {
                  setAssignmentStatusFilter(e.target.value);
                  setAssignmentPage(1);
                }}
                className="px-3 py-1.5 text-xs bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">All Assignment Statuses</option>
                <option value="ACTIVE">Active Custody</option>
                <option value="RETURNED">Returned</option>
                <option value="TRANSFERRED">Transferred</option>
              </select>
            </div>

            {canIssue && (
              <Button
                size="sm"
                onClick={() => {
                  setAssignFormData({
                    asset_id: assets.find((a) => a.status === 'AVAILABLE')?.id || assets[0]?.id || '',
                    assignment_type: 'STAFF',
                    assigned_date: new Date().toISOString().split('T')[0],
                    expected_return_date: '',
                    condition_on_assignment: 'GOOD',
                    remarks: '',
                  });
                  setShowAssignModal(true);
                }}
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Assign Asset
              </Button>
            )}
          </div>

          <Card>
            <CardContent className="p-0">
              {loadingAssignments && <LoadingState message="Loading custody assignments..." />}
              {assignmentError && <ErrorState message={assignmentError} onRetry={fetchAssignments} />}

              {!loadingAssignments && !assignmentError && assignments.length === 0 && (
                <EmptyState
                  title="No assignments recorded"
                  description="Issue assets to faculty, students, classrooms or departments."
                />
              )}

              {!loadingAssignments && !assignmentError && assignments.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-paper-dim border-b border-divider text-ink-muted uppercase font-mono text-[10px]">
                      <tr>
                        <th className="px-4 py-3">Asset Tag</th>
                        <th className="px-4 py-3">Item</th>
                        <th className="px-4 py-3">Target Type</th>
                        <th className="px-4 py-3">Custodian Target</th>
                        <th className="px-4 py-3">Assigned Date</th>
                        <th className="px-4 py-3">Expected Return</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-divider">
                      {assignments.map((asg) => {
                        let targetLabel = '—';
                        if (asg.assignment_type === 'STAFF') {
                          const t = teachersList.find((x) => x.id === asg.teacher_id);
                          const u = usersList.find((x) => x.id === asg.user_id);
                          targetLabel = t ? `${t.first_name} ${t.last_name}` : u ? (u.username || u.email) : 'Staff Member';
                        } else if (asg.assignment_type === 'STUDENT') {
                          const s = studentsList.find((x) => x.id === asg.student_id);
                          targetLabel = s ? `${s.first_name} ${s.last_name}` : 'Student';
                        } else if (asg.assignment_type === 'CLASSROOM') {
                          const c = classroomsList.find((x) => x.id === asg.classroom_id);
                          targetLabel = c ? (c.building_name ? `${c.room_number} (${c.building_name})` : c.room_number) : 'Classroom';
                        } else if (asg.assignment_type === 'DEPARTMENT') {
                          targetLabel = asg.department_name || 'Department';
                        }

                        return (
                          <tr key={asg.id} className="hover:bg-paper-hover">
                            <td className="px-4 py-3 font-mono font-bold text-brand-600 dark:text-brand-400">
                              {asg.asset?.asset_tag || '—'}
                            </td>
                            <td className="px-4 py-3 font-medium text-ink">{asg.asset?.item?.name || '—'}</td>
                            <td className="px-4 py-3">
                              <Badge variant="neutral">{asg.assignment_type}</Badge>
                            </td>
                            <td className="px-4 py-3 font-medium text-ink">{targetLabel}</td>
                            <td className="px-4 py-3 font-mono text-ink-muted">{asg.assigned_date}</td>
                            <td className="px-4 py-3 font-mono text-ink-muted">
                              {asg.expected_return_date || 'Permanent'}
                            </td>
                            <td className="px-4 py-3">
                              <Badge
                                variant={
                                  asg.status === 'ACTIVE'
                                    ? 'success'
                                    : asg.status === 'RETURNED'
                                    ? 'neutral'
                                    : 'info'
                                }
                              >
                                {asg.status}
                              </Badge>
                            </td>
                            <td className="px-4 py-3 text-right space-x-1.5">
                              {canIssue && asg.status === 'ACTIVE' && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    setSelectedAssignmentForReturn(asg);
                                    setReturnAssignmentForm({
                                      actual_return_date: new Date().toISOString().split('T')[0],
                                      condition_on_return: asg.condition_on_assignment,
                                      return_location_id: asg.asset?.location_id || undefined,
                                      remarks: '',
                                    });
                                    setShowReturnAssignmentModal(true);
                                  }}
                                >
                                  Return
                                </Button>
                              )}

                              {canTransfer && asg.status === 'ACTIVE' && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    setSelectedAssignmentForTransfer(asg);
                                    setTransferAssignmentForm({
                                      new_assignment_type: 'STAFF',
                                      new_teacher_id: undefined,
                                      new_student_id: undefined,
                                      new_classroom_id: undefined,
                                      new_user_id: undefined,
                                      new_department_name: '',
                                      transfer_date: new Date().toISOString().split('T')[0],
                                      condition: asg.condition_on_assignment,
                                      remarks: '',
                                    });
                                    setShowTransferAssignmentModal(true);
                                  }}
                                >
                                  Transfer
                                </Button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {assignmentTotalPages > 1 && (
            <Pagination
              page={assignmentPage}
              totalPages={assignmentTotalPages}
              onPageChange={setAssignmentPage}
            />
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* 6. STORAGE LOCATIONS */}
      {/* ===================================================================== */}
      {activeTab === 'locations' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2.5 flex-1">
              <div className="relative w-64">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-ink-muted" />
                <Input
                  placeholder="Search location name, code, building..."
                  value={locationSearch}
                  onChange={(e) => {
                    setLocationSearch(e.target.value);
                    setLocationPage(1);
                  }}
                  className="pl-9 text-xs"
                />
              </div>

              <select
                value={locationTypeFilter}
                onChange={(e) => {
                  setLocationTypeFilter(e.target.value);
                  setLocationPage(1);
                }}
                className="px-3 py-1.5 text-xs bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">All Types</option>
                <option value="WAREHOUSE">Warehouse</option>
                <option value="STORE_ROOM">Store Room</option>
                <option value="LAB">Laboratory</option>
                <option value="LIBRARY_STORE">Library Store</option>
                <option value="OFFICE">Office</option>
                <option value="CLASSROOM">Classroom</option>
                <option value="SPORTS_ROOM">Sports Room</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            {canCreate && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingLocation(null);
                  setLocationFormData({
                    name: '',
                    code: '',
                    location_type: 'STORE_ROOM',
                    parent_location_id: undefined,
                    building_name: '',
                    description: '',
                    is_active: true,
                  });
                  setShowLocationModal(true);
                }}
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Add Location
              </Button>
            )}
          </div>

          <Card>
            <CardContent className="p-0">
              {loadingLocations && <LoadingState message="Loading storage locations..." />}
              {locationError && <ErrorState message={locationError} onRetry={fetchLocations} />}

              {!loadingLocations && !locationError && locationsList.length === 0 && (
                <EmptyState
                  title="No locations configured"
                  description="Define warehouses, store rooms, and department lockers."
                />
              )}

              {!loadingLocations && !locationError && locationsList.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-paper-dim border-b border-divider text-ink-muted uppercase font-mono text-[10px]">
                      <tr>
                        <th className="px-4 py-3">Code</th>
                        <th className="px-4 py-3">Name</th>
                        <th className="px-4 py-3">Type</th>
                        <th className="px-4 py-3">Building</th>
                        <th className="px-4 py-3">Parent Location</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-divider">
                      {locationsList.map((loc) => {
                        const parent = locations.find((p) => p.id === loc.parent_location_id);

                        return (
                          <tr key={loc.id} className="hover:bg-paper-hover">
                            <td className="px-4 py-3 font-mono font-medium text-ink">{loc.code}</td>
                            <td className="px-4 py-3 font-medium text-ink">{loc.name}</td>
                            <td className="px-4 py-3">
                              <Badge variant="neutral">{loc.location_type}</Badge>
                            </td>
                            <td className="px-4 py-3 text-ink-muted">{loc.building_name || '—'}</td>
                            <td className="px-4 py-3 text-ink-muted">{parent ? parent.name : '— (Root)'}</td>
                            <td className="px-4 py-3">
                              <Badge variant={loc.is_active ? 'success' : 'neutral'}>
                                {loc.is_active ? 'Active' : 'Inactive'}
                              </Badge>
                            </td>
                            <td className="px-4 py-3 text-right space-x-1.5">
                              {canUpdate && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    setEditingLocation(loc);
                                    setLocationFormData({
                                      name: loc.name,
                                      code: loc.code,
                                      location_type: loc.location_type,
                                      parent_location_id: loc.parent_location_id || undefined,
                                      building_name: loc.building_name || '',
                                      description: loc.description || '',
                                      is_active: loc.is_active,
                                    });
                                    setShowLocationModal(true);
                                  }}
                                >
                                  <Edit2 className="w-3.5 h-3.5" />
                                </Button>
                              )}
                              {canDelete && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="text-rose-600 hover:text-rose-700"
                                  onClick={() => setDeletingLocationId(loc.id)}
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </Button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {locationTotalPages > 1 && (
            <Pagination
              page={locationPage}
              totalPages={locationTotalPages}
              onPageChange={setLocationPage}
            />
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* 7. VENDORS */}
      {/* ===================================================================== */}
      {activeTab === 'vendors' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between gap-3">
            <div className="relative w-64">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-ink-muted" />
              <Input
                placeholder="Search vendor name, contact, email..."
                value={vendorSearch}
                onChange={(e) => {
                  setVendorSearch(e.target.value);
                  setVendorPage(1);
                }}
                className="pl-9 text-xs"
              />
            </div>

            {canCreate && (
              <Button
                size="sm"
                onClick={() => {
                  setEditingVendor(null);
                  setVendorFormData({
                    name: '',
                    code: '',
                    contact_name: '',
                    email: '',
                    phone: '',
                    address: '',
                    tax_id: '',
                    is_active: true,
                  });
                  setShowVendorModal(true);
                }}
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Add Vendor
              </Button>
            )}
          </div>

          <Card>
            <CardContent className="p-0">
              {loadingVendors && <LoadingState message="Loading supplier directory..." />}
              {vendorError && <ErrorState message={vendorError} onRetry={fetchVendors} />}

              {!loadingVendors && !vendorError && vendorsList.length === 0 && (
                <EmptyState
                  title="No vendors found"
                  description="Register suppliers to trace procurement receipts and warranty claims."
                />
              )}

              {!loadingVendors && !vendorError && vendorsList.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-paper-dim border-b border-divider text-ink-muted uppercase font-mono text-[10px]">
                      <tr>
                        <th className="px-4 py-3">Code</th>
                        <th className="px-4 py-3">Vendor Name</th>
                        <th className="px-4 py-3">Contact Person</th>
                        <th className="px-4 py-3">Email & Phone</th>
                        <th className="px-4 py-3">Tax ID</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-divider">
                      {vendorsList.map((v) => (
                        <tr key={v.id} className="hover:bg-paper-hover">
                          <td className="px-4 py-3 font-mono font-medium text-ink">{v.code}</td>
                          <td className="px-4 py-3 font-medium text-ink">{v.name}</td>
                          <td className="px-4 py-3 text-ink-muted">{v.contact_name || '—'}</td>
                          <td className="px-4 py-3 text-ink-muted">
                            <div>{v.email || '—'}</div>
                            <div className="text-[10px]">{v.phone || '—'}</div>
                          </td>
                          <td className="px-4 py-3 font-mono text-ink-muted">{v.tax_id || '—'}</td>
                          <td className="px-4 py-3">
                            <Badge variant={v.is_active ? 'success' : 'neutral'}>
                              {v.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-right space-x-1.5">
                            {canUpdate && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setEditingVendor(v);
                                  setVendorFormData({
                                    name: v.name,
                                    code: v.code,
                                    contact_name: v.contact_name || '',
                                    email: v.email || '',
                                    phone: v.phone || '',
                                    address: v.address || '',
                                    tax_id: v.tax_id || '',
                                    is_active: v.is_active,
                                  });
                                  setShowVendorModal(true);
                                }}
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </Button>
                            )}
                            {canDelete && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-rose-600 hover:text-rose-700"
                                onClick={() => setDeletingVendorId(v.id)}
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {vendorTotalPages > 1 && (
            <Pagination page={vendorPage} totalPages={vendorTotalPages} onPageChange={setVendorPage} />
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* 8. MOVEMENT HISTORY (AUDIT TRAIL) */}
      {/* ===================================================================== */}
      {activeTab === 'movements' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2.5">
            <select
              value={movementTypeFilter}
              onChange={(e) => {
                setMovementTypeFilter(e.target.value);
                setMovementPage(1);
              }}
              className="px-3 py-1.5 text-xs bg-paper border border-divider rounded-md text-ink"
            >
              <option value="">All Movement Types</option>
              <option value="PURCHASE_RECEIPT">Receipt</option>
              <option value="ISSUE">Issue</option>
              <option value="TRANSFER">Transfer</option>
              <option value="RETURN">Return</option>
              <option value="ADJUSTMENT">Adjustment</option>
              <option value="DISCARD">Discard</option>
            </select>

            <select
              value={movementItemFilter}
              onChange={(e) => {
                setMovementItemFilter(e.target.value);
                setMovementPage(1);
              }}
              className="px-3 py-1.5 text-xs bg-paper border border-divider rounded-md text-ink"
            >
              <option value="">All Items</option>
              {allItemsList.map((itm) => (
                <option key={itm.id} value={itm.id}>
                  {itm.name} ({itm.item_code})
                </option>
              ))}
            </select>

            <div className="relative w-56">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-ink-muted" />
              <Input
                placeholder="Filter reference #..."
                value={movementRefFilter}
                onChange={(e) => {
                  setMovementRefFilter(e.target.value);
                  setMovementPage(1);
                }}
                className="pl-9 text-xs"
              />
            </div>
          </div>

          <Card>
            <CardContent className="p-0">
              {loadingMovements && <LoadingState message="Loading audit trail..." />}
              {movementError && <ErrorState message={movementError} onRetry={fetchMovements} />}

              {!loadingMovements && !movementError && movements.length === 0 && (
                <EmptyState
                  title="No stock movements recorded"
                  description="All receipts, issues, transfers, and adjustments are securely audited here."
                />
              )}

              {!loadingMovements && !movementError && movements.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-paper-dim border-b border-divider text-ink-muted uppercase font-mono text-[10px]">
                      <tr>
                        <th className="px-4 py-3">Timestamp</th>
                        <th className="px-4 py-3">Item</th>
                        <th className="px-4 py-3">Type</th>
                        <th className="px-4 py-3">Quantity</th>
                        <th className="px-4 py-3">Source Location</th>
                        <th className="px-4 py-3">Destination Location</th>
                        <th className="px-4 py-3">Ref / Remarks</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-divider">
                      {movements.map((m) => (
                        <tr key={m.id} className="hover:bg-paper-hover">
                          <td className="px-4 py-3 font-mono text-ink-muted whitespace-nowrap">
                            {new Date(m.movement_date).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 font-medium text-ink">
                            <div>{m.item?.name}</div>
                            <div className="text-[10px] text-ink-muted">{m.item?.item_code}</div>
                          </td>
                          <td className="px-4 py-3">{getMovementBadge(m.movement_type)}</td>
                          <td className="px-4 py-3 font-mono font-bold text-ink">
                            {m.quantity} {m.item?.unit_of_measure}
                          </td>
                          <td className="px-4 py-3 text-ink-muted">{m.source_location?.name || '—'}</td>
                          <td className="px-4 py-3 text-ink-muted">{m.destination_location?.name || '—'}</td>
                          <td className="px-4 py-3 text-ink-muted">
                            <div className="font-mono text-ink">{m.reference_number || '—'}</div>
                            <div className="text-[11px] truncate max-w-xs">{m.remarks || ''}</div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {movementTotalPages > 1 && (
            <Pagination page={movementPage} totalPages={movementTotalPages} onPageChange={setMovementPage} />
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* MODALS */}
      {/* ===================================================================== */}

      {/* Item Create/Edit Modal */}
      <Modal
        isOpen={showItemModal}
        onClose={() => setShowItemModal(false)}
        title={editingItem ? 'Edit Item' : 'Add Item to Catalog'}
      >
        <form onSubmit={handleSaveItem} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Item Code *</label>
              <Input
                required
                value={itemFormData.item_code}
                onChange={(e) => setItemFormData({ ...itemFormData, item_code: e.target.value })}
                placeholder="e.g. ITM-LAP-001"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Item Name *</label>
              <Input
                required
                value={itemFormData.name}
                onChange={(e) => setItemFormData({ ...itemFormData, name: e.target.value })}
                placeholder="e.g. Dell Latitude 3420"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Category *</label>
              <select
                required
                value={itemFormData.category_id}
                onChange={(e) => setItemFormData({ ...itemFormData, category_id: e.target.value })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Item Type *</label>
              <select
                value={itemFormData.item_type}
                onChange={(e) =>
                  setItemFormData({ ...itemFormData, item_type: e.target.value as InventoryItemType })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="CONSUMABLE">Consumable</option>
                <option value="ASSET">Physical Asset</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Unit of Measure *</label>
              <Input
                required
                value={itemFormData.unit_of_measure}
                onChange={(e) => setItemFormData({ ...itemFormData, unit_of_measure: e.target.value })}
                placeholder="PCS, BOX, KG, LTR"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Reorder Alert Threshold</label>
              <Input
                type="number"
                min="0"
                value={itemFormData.reorder_level}
                onChange={(e) => setItemFormData({ ...itemFormData, reorder_level: Number(e.target.value) })}
              />
            </div>
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Description</label>
            <textarea
              rows={2}
              value={itemFormData.description || ''}
              onChange={(e) => setItemFormData({ ...itemFormData, description: e.target.value })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              placeholder="Technical specifications or notes..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowItemModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Item'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Receive Stock Modal */}
      <Modal
        isOpen={showReceiveModal}
        onClose={() => setShowReceiveModal(false)}
        title="Receive Stock (Purchase Receipt)"
      >
        <form onSubmit={handleReceiveStock} className="space-y-4 text-xs">
          <div>
            <label className="block font-medium text-ink mb-1">Item *</label>
            <select
              required
              value={receiveForm.item_id}
              onChange={(e) => setReceiveForm({ ...receiveForm, item_id: e.target.value })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
            >
              <option value="">Select Item</option>
              {allItemsList.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name} ({i.item_code})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Destination Location *</label>
              <select
                required
                value={receiveForm.location_id}
                onChange={(e) => setReceiveForm({ ...receiveForm, location_id: e.target.value })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Location</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Quantity Received *</label>
              <Input
                type="number"
                min="1"
                required
                value={receiveForm.quantity}
                onChange={(e) => setReceiveForm({ ...receiveForm, quantity: Number(e.target.value) })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Supplier / Vendor</label>
              <select
                value={receiveForm.vendor_id || ''}
                onChange={(e) => setReceiveForm({ ...receiveForm, vendor_id: e.target.value || undefined })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Vendor (Optional)</option>
                {vendors.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Unit Price ($)</label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={receiveForm.unit_price ?? ''}
                onChange={(e) =>
                  setReceiveForm({
                    ...receiveForm,
                    unit_price: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                placeholder="0.00"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">PO / Invoice #</label>
              <Input
                value={receiveForm.reference_number || ''}
                onChange={(e) => setReceiveForm({ ...receiveForm, reference_number: e.target.value })}
                placeholder="e.g. INV-2026-004"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Remarks</label>
              <Input
                value={receiveForm.remarks || ''}
                onChange={(e) => setReceiveForm({ ...receiveForm, remarks: e.target.value })}
                placeholder="Optional notes"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowReceiveModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Receiving...' : 'Confirm Receipt'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Issue Stock Modal */}
      <Modal isOpen={showIssueModal} onClose={() => setShowIssueModal(false)} title="Issue Stock (Consumables)">
        <form onSubmit={handleIssueStock} className="space-y-4 text-xs">
          <div>
            <label className="block font-medium text-ink mb-1">Item *</label>
            <select
              required
              value={issueForm.item_id}
              onChange={(e) => setIssueForm({ ...issueForm, item_id: e.target.value })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
            >
              <option value="">Select Item</option>
              {allItemsList.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name} ({i.item_code})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Source Location *</label>
              <select
                required
                value={issueForm.location_id}
                onChange={(e) => setIssueForm({ ...issueForm, location_id: e.target.value })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Location</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Quantity to Issue *</label>
              <Input
                type="number"
                min="1"
                required
                value={issueForm.quantity}
                onChange={(e) => setIssueForm({ ...issueForm, quantity: Number(e.target.value) })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Requisition / Ref #</label>
              <Input
                value={issueForm.reference_number || ''}
                onChange={(e) => setIssueForm({ ...issueForm, reference_number: e.target.value })}
                placeholder="e.g. REQ-SCIENCE-01"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Remarks / Department</label>
              <Input
                value={issueForm.remarks || ''}
                onChange={(e) => setIssueForm({ ...issueForm, remarks: e.target.value })}
                placeholder="e.g. Physics Lab consumable"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowIssueModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Issuing...' : 'Confirm Issue'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Return Stock Modal */}
      <Modal
        isOpen={showReturnModal}
        onClose={() => setShowReturnModal(false)}
        title="Return Issued Stock to Location"
      >
        <form onSubmit={handleReturnStock} className="space-y-4 text-xs">
          <div>
            <label className="block font-medium text-ink mb-1">Item *</label>
            <select
              required
              value={returnStockForm.item_id}
              onChange={(e) => setReturnStockForm({ ...returnStockForm, item_id: e.target.value })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
            >
              <option value="">Select Item</option>
              {allItemsList.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name} ({i.item_code})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Return Location *</label>
              <select
                required
                value={returnStockForm.location_id}
                onChange={(e) => setReturnStockForm({ ...returnStockForm, location_id: e.target.value })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Location</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Quantity Returned *</label>
              <Input
                type="number"
                min="1"
                required
                value={returnStockForm.quantity}
                onChange={(e) => setReturnStockForm({ ...returnStockForm, quantity: Number(e.target.value) })}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Reference #</label>
              <Input
                value={returnStockForm.reference_number || ''}
                onChange={(e) => setReturnStockForm({ ...returnStockForm, reference_number: e.target.value })}
                placeholder="e.g. RET-LAB-01"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Remarks</label>
              <Input
                value={returnStockForm.remarks || ''}
                onChange={(e) => setReturnStockForm({ ...returnStockForm, remarks: e.target.value })}
                placeholder="Unused supplies returned"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowReturnModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Returning...' : 'Confirm Return'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Adjust Stock Modal */}
      <Modal isOpen={showAdjustModal} onClose={() => setShowAdjustModal(false)} title="Audit Stock Adjustment">
        <form onSubmit={handleAdjustStock} className="space-y-4 text-xs">
          <div>
            <label className="block font-medium text-ink mb-1">Item *</label>
            <select
              required
              value={adjustForm.item_id}
              onChange={(e) => setAdjustForm({ ...adjustForm, item_id: e.target.value })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
            >
              <option value="">Select Item</option>
              {allItemsList.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name} ({i.item_code})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Location *</label>
              <select
                required
                value={adjustForm.location_id}
                onChange={(e) => setAdjustForm({ ...adjustForm, location_id: e.target.value })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Location</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Action Type *</label>
              <select
                value={adjustForm.adjustment_type}
                onChange={(e) =>
                  setAdjustForm({ ...adjustForm, adjustment_type: e.target.value as 'ADD' | 'SUBTRACT' })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="ADD">ADD (+ Increase Balance)</option>
                <option value="SUBTRACT">SUBTRACT (- Decrease Balance)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Adjustment Quantity *</label>
              <Input
                type="number"
                min="1"
                required
                value={adjustForm.quantity}
                onChange={(e) => setAdjustForm({ ...adjustForm, quantity: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Reference Number</label>
              <Input
                value={adjustForm.reference_number || ''}
                onChange={(e) => setAdjustForm({ ...adjustForm, reference_number: e.target.value })}
                placeholder="e.g. AUDIT-2026-Q1"
              />
            </div>
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Mandatory Audit Reason *</label>
            <textarea
              required
              rows={2}
              value={adjustForm.reason}
              onChange={(e) => setAdjustForm({ ...adjustForm, reason: e.target.value })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              placeholder="e.g. Physical inventory count reconciliation or damaged goods removal"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowAdjustModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Adjusting...' : 'Confirm Adjustment'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Transfer Stock Modal */}
      <Modal isOpen={showTransferModal} onClose={() => setShowTransferModal(false)} title="Transfer Stock Between Locations">
        <form onSubmit={handleTransferStock} className="space-y-4 text-xs">
          <div>
            <label className="block font-medium text-ink mb-1">Item *</label>
            <select
              required
              value={transferStockForm.item_id}
              onChange={(e) => setTransferStockForm({ ...transferStockForm, item_id: e.target.value })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
            >
              <option value="">Select Item</option>
              {allItemsList.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name} ({i.item_code})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Source Location *</label>
              <select
                required
                value={transferStockForm.source_location_id}
                onChange={(e) =>
                  setTransferStockForm({ ...transferStockForm, source_location_id: e.target.value })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Source</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Destination Location *</label>
              <select
                required
                value={transferStockForm.destination_location_id}
                onChange={(e) =>
                  setTransferStockForm({ ...transferStockForm, destination_location_id: e.target.value })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Destination</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Transfer Quantity *</label>
              <Input
                type="number"
                min="1"
                required
                value={transferStockForm.quantity}
                onChange={(e) =>
                  setTransferStockForm({ ...transferStockForm, quantity: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Reference Number</label>
              <Input
                value={transferStockForm.reference_number || ''}
                onChange={(e) =>
                  setTransferStockForm({ ...transferStockForm, reference_number: e.target.value })}
                placeholder="e.g. TR-2026-08"
              />
            </div>
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Remarks</label>
            <Input
              value={transferStockForm.remarks || ''}
              onChange={(e) => setTransferStockForm({ ...transferStockForm, remarks: e.target.value })}
              placeholder="e.g. Lab replenishment from main warehouse"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowTransferModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Transferring...' : 'Execute Transfer'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Asset Create/Edit Modal */}
      <Modal
        isOpen={showAssetModal}
        onClose={() => setShowAssetModal(false)}
        title={editingAsset ? 'Edit Asset' : 'Register Physical Asset'}
      >
        <form onSubmit={handleSaveAsset} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Asset Tag *</label>
              <Input
                required
                value={assetFormData.asset_tag}
                onChange={(e) => setAssetFormData({ ...assetFormData, asset_tag: e.target.value })}
                placeholder="e.g. TAG-2026-001"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Catalog Item *</label>
              <select
                required
                value={assetFormData.item_id}
                onChange={(e) => setAssetFormData({ ...assetFormData, item_id: e.target.value })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Item</option>
                {allItemsList.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.name} ({i.item_code})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Serial Number</label>
              <Input
                value={assetFormData.serial_number || ''}
                onChange={(e) => setAssetFormData({ ...assetFormData, serial_number: e.target.value })}
                placeholder="e.g. SN-84920492"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Model Number</label>
              <Input
                value={assetFormData.model_number || ''}
                onChange={(e) => setAssetFormData({ ...assetFormData, model_number: e.target.value })}
                placeholder="e.g. XPS-13-9310"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Location</label>
              <select
                value={assetFormData.location_id || ''}
                onChange={(e) => setAssetFormData({ ...assetFormData, location_id: e.target.value || undefined })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Unassigned Location</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Vendor / Supplier</label>
              <select
                value={assetFormData.vendor_id || ''}
                onChange={(e) => setAssetFormData({ ...assetFormData, vendor_id: e.target.value || undefined })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Vendor (Optional)</option>
                {vendors.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Asset Status</label>
              <select
                value={assetFormData.status}
                onChange={(e) => setAssetFormData({ ...assetFormData, status: e.target.value as AssetStatus })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="AVAILABLE">Available</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="IN_REPAIR">In Repair</option>
                <option value="DAMAGED">Damaged</option>
                <option value="LOST">Lost</option>
                <option value="RETIRED">Retired</option>
                <option value="DISPOSED">Disposed</option>
              </select>
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Physical Condition</label>
              <select
                value={assetFormData.condition}
                onChange={(e) =>
                  setAssetFormData({ ...assetFormData, condition: e.target.value as AssetCondition })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="EXCELLENT">Excellent</option>
                <option value="GOOD">Good</option>
                <option value="FAIR">Fair</option>
                <option value="POOR">Poor</option>
                <option value="DAMAGED">Damaged</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Purchase Date</label>
              <Input
                type="date"
                value={assetFormData.purchase_date || ''}
                onChange={(e) => setAssetFormData({ ...assetFormData, purchase_date: e.target.value })}
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Cost ($)</label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={assetFormData.purchase_cost ?? ''}
                onChange={(e) =>
                  setAssetFormData({
                    ...assetFormData,
                    purchase_cost: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Warranty Expiry</label>
              <Input
                type="date"
                value={assetFormData.warranty_expiry_date || ''}
                onChange={(e) => setAssetFormData({ ...assetFormData, warranty_expiry_date: e.target.value })}
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowAssetModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Asset'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Retire Asset Modal */}
      <Modal
        isOpen={showRetireModal}
        onClose={() => setShowRetireModal(false)}
        title="Retire / Dispose Asset"
      >
        <form onSubmit={handleRetireAsset} className="space-y-4 text-xs">
          <div>
            <label className="block font-medium text-ink mb-1">Target Lifecycle State</label>
            <select
              value={retireForm.status}
              onChange={(e) => setRetireForm({ ...retireForm, status: e.target.value as AssetStatus })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
            >
              <option value="RETIRED">Retired (End of Life)</option>
              <option value="DISPOSED">Disposed (Scrapped/Sold)</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Disposal Reason / Remarks</label>
            <textarea
              rows={3}
              value={retireForm.notes || ''}
              onChange={(e) => setRetireForm({ ...retireForm, notes: e.target.value })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              placeholder="e.g. Hardware failure beyond economical repair..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowRetireModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="danger" disabled={isSubmitting}>
              {isSubmitting ? 'Updating...' : 'Confirm Status Change'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Asset History Modal */}
      <Modal
        isOpen={showAssetHistoryModal}
        onClose={() => setShowAssetHistoryModal(false)}
        title={`Custody History — ${selectedAssetForHistory?.asset_tag || ''}`}
      >
        <div className="space-y-4 text-xs">
          {loadingHistory && <LoadingState message="Loading assignment history..." />}
          {!loadingHistory && assetHistoryList.length === 0 && (
            <p className="text-ink-muted text-center py-4">No assignment records for this asset.</p>
          )}

          {!loadingHistory && assetHistoryList.length > 0 && (
            <div className="divide-y divide-divider max-h-96 overflow-y-auto">
              {assetHistoryList.map((h) => (
                <div key={h.id} className="py-2.5 space-y-1">
                  <div className="flex justify-between font-medium text-ink">
                    <span>
                      {h.assignment_type}: {h.department_name || 'Custodian'}
                    </span>
                    <Badge variant={h.status === 'ACTIVE' ? 'success' : 'neutral'}>{h.status}</Badge>
                  </div>
                  <div className="text-[11px] text-ink-muted flex justify-between">
                    <span>Assigned: {h.assigned_date}</span>
                    <span>Returned: {h.actual_return_date || 'In Custody'}</span>
                  </div>
                  {h.remarks && <p className="text-[11px] text-ink-muted italic">"{h.remarks}"</p>}
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end pt-2 border-t border-divider">
            <Button variant="outline" onClick={() => setShowAssetHistoryModal(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>

      {/* Asset Assignment Modal */}
      <Modal isOpen={showAssignModal} onClose={() => setShowAssignModal(false)} title="Assign Asset to Custodian">
        <form onSubmit={handleCreateAssignment} className="space-y-4 text-xs">
          <div>
            <label className="block font-medium text-ink mb-1">Select Available Asset *</label>
            <select
              required
              value={assignFormData.asset_id}
              onChange={(e) => setAssignFormData({ ...assignFormData, asset_id: e.target.value })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
            >
              <option value="">Select Asset</option>
              {assets
                .filter((a) => a.status === 'AVAILABLE')
                .map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.asset_tag} — {a.item?.name} (SN: {a.serial_number || 'N/A'})
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Assignment Target Type *</label>
            <select
              value={assignFormData.assignment_type}
              onChange={(e) =>
                setAssignFormData({
                  ...assignFormData,
                  assignment_type: e.target.value as AssetAssignmentType,
                  teacher_id: undefined,
                  student_id: undefined,
                  classroom_id: undefined,
                  user_id: undefined,
                  department_name: '',
                })
              }
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
            >
              <option value="STAFF">Teacher / Faculty</option>
              <option value="STUDENT">Student</option>
              <option value="CLASSROOM">Classroom</option>
              <option value="DEPARTMENT">Department</option>
            </select>
          </div>

          {/* Dynamic Target Selectors */}
          {assignFormData.assignment_type === 'STAFF' && (
            <div>
              <label className="block font-medium text-ink mb-1">Select Teacher / Staff *</label>
              <select
                value={assignFormData.teacher_id || ''}
                onChange={(e) => setAssignFormData({ ...assignFormData, teacher_id: e.target.value || undefined })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Teacher</option>
                {teachersList.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.first_name} {t.last_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {assignFormData.assignment_type === 'STUDENT' && (
            <div>
              <label className="block font-medium text-ink mb-1">Select Student *</label>
              <select
                value={assignFormData.student_id || ''}
                onChange={(e) => setAssignFormData({ ...assignFormData, student_id: e.target.value || undefined })}
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Student</option>
                {studentsList.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.first_name} {s.last_name} ({s.admission_number})
                  </option>
                ))}
              </select>
            </div>
          )}

          {assignFormData.assignment_type === 'CLASSROOM' && (
            <div>
              <label className="block font-medium text-ink mb-1">Select Classroom *</label>
              <select
                value={assignFormData.classroom_id || ''}
                onChange={(e) =>
                  setAssignFormData({ ...assignFormData, classroom_id: e.target.value || undefined })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Classroom</option>
                {classroomsList.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.room_number} ({c.building_name || 'Classroom'})
                  </option>
                ))}
              </select>
            </div>
          )}

          {assignFormData.assignment_type === 'DEPARTMENT' && (
            <div>
              <label className="block font-medium text-ink mb-1">Department Name *</label>
              <Input
                required
                value={assignFormData.department_name || ''}
                onChange={(e) => setAssignFormData({ ...assignFormData, department_name: e.target.value })}
                placeholder="e.g. Science Lab, Administration, Sports Dept"
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Assigned Date *</label>
              <Input
                type="date"
                required
                value={assignFormData.assigned_date}
                onChange={(e) => setAssignFormData({ ...assignFormData, assigned_date: e.target.value })}
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Expected Return Date</label>
              <Input
                type="date"
                value={assignFormData.expected_return_date || ''}
                onChange={(e) => setAssignFormData({ ...assignFormData, expected_return_date: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Remarks</label>
            <Input
              value={assignFormData.remarks || ''}
              onChange={(e) => setAssignFormData({ ...assignFormData, remarks: e.target.value })}
              placeholder="e.g. Handed over with charger and bag"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowAssignModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Assigning...' : 'Assign Asset'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Return Assignment Modal */}
      <Modal
        isOpen={showReturnAssignmentModal}
        onClose={() => setShowReturnAssignmentModal(false)}
        title="Return Asset to School Custody"
      >
        <form onSubmit={handleReturnAssignment} className="space-y-4 text-xs">
          <div className="p-3 bg-paper-dim rounded-md text-ink">
            <span className="font-semibold">Asset: </span>
            {selectedAssignmentForReturn?.asset?.asset_tag} — {selectedAssignmentForReturn?.asset?.item?.name}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Return Date *</label>
              <Input
                type="date"
                required
                value={returnAssignmentForm.actual_return_date}
                onChange={(e) =>
                  setReturnAssignmentForm({ ...returnAssignmentForm, actual_return_date: e.target.value })
                }
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Condition on Return *</label>
              <select
                value={returnAssignmentForm.condition_on_return}
                onChange={(e) =>
                  setReturnAssignmentForm({
                    ...returnAssignmentForm,
                    condition_on_return: e.target.value as AssetCondition,
                  })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="EXCELLENT">Excellent</option>
                <option value="GOOD">Good</option>
                <option value="FAIR">Fair</option>
                <option value="POOR">Poor</option>
                <option value="DAMAGED">Damaged</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Return Location</label>
            <select
              value={returnAssignmentForm.return_location_id || ''}
              onChange={(e) =>
                setReturnAssignmentForm({
                  ...returnAssignmentForm,
                  return_location_id: e.target.value || undefined,
                })
              }
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
            >
              <option value="">Select Return Store / Room</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Return Remarks</label>
            <Input
              value={returnAssignmentForm.remarks || ''}
              onChange={(e) => setReturnAssignmentForm({ ...returnAssignmentForm, remarks: e.target.value })}
              placeholder="e.g. Asset returned in full working condition"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowReturnAssignmentModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Returning...' : 'Confirm Asset Return'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Transfer Assignment Modal */}
      <Modal
        isOpen={showTransferAssignmentModal}
        onClose={() => setShowTransferAssignmentModal(false)}
        title="Transfer Asset Assignment"
      >
        <form onSubmit={handleTransferAssignment} className="space-y-4 text-xs">
          <div className="p-3 bg-paper-dim rounded-md text-ink">
            <span className="font-semibold">Asset: </span>
            {selectedAssignmentForTransfer?.asset?.asset_tag} — {selectedAssignmentForTransfer?.asset?.item?.name}
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">New Target Type *</label>
            <select
              value={transferAssignmentForm.new_assignment_type}
              onChange={(e) =>
                setTransferAssignmentForm({
                  ...transferAssignmentForm,
                  new_assignment_type: e.target.value as AssetAssignmentType,
                  new_teacher_id: undefined,
                  new_student_id: undefined,
                  new_classroom_id: undefined,
                  new_user_id: undefined,
                  new_department_name: '',
                })
              }
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
            >
              <option value="STAFF">Teacher / Faculty</option>
              <option value="STUDENT">Student</option>
              <option value="CLASSROOM">Classroom</option>
              <option value="DEPARTMENT">Department</option>
            </select>
          </div>

          {/* Transfer Target Selectors */}
          {transferAssignmentForm.new_assignment_type === 'STAFF' && (
            <div>
              <label className="block font-medium text-ink mb-1">Select New Teacher *</label>
              <select
                value={transferAssignmentForm.new_teacher_id || ''}
                onChange={(e) =>
                  setTransferAssignmentForm({
                    ...transferAssignmentForm,
                    new_teacher_id: e.target.value || undefined,
                  })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Teacher</option>
                {teachersList.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.first_name} {t.last_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {transferAssignmentForm.new_assignment_type === 'STUDENT' && (
            <div>
              <label className="block font-medium text-ink mb-1">Select New Student *</label>
              <select
                value={transferAssignmentForm.new_student_id || ''}
                onChange={(e) =>
                  setTransferAssignmentForm({
                    ...transferAssignmentForm,
                    new_student_id: e.target.value || undefined,
                  })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Student</option>
                {studentsList.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.first_name} {s.last_name} ({s.admission_number})
                  </option>
                ))}
              </select>
            </div>
          )}

          {transferAssignmentForm.new_assignment_type === 'CLASSROOM' && (
            <div>
              <label className="block font-medium text-ink mb-1">Select New Classroom *</label>
              <select
                value={transferAssignmentForm.new_classroom_id || ''}
                onChange={(e) =>
                  setTransferAssignmentForm({
                    ...transferAssignmentForm,
                    new_classroom_id: e.target.value || undefined,
                  })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">Select Classroom</option>
                {classroomsList.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.room_number} ({c.building_name || 'Classroom'})
                  </option>
                ))}
              </select>
            </div>
          )}

          {transferAssignmentForm.new_assignment_type === 'DEPARTMENT' && (
            <div>
              <label className="block font-medium text-ink mb-1">New Department Name *</label>
              <Input
                required
                value={transferAssignmentForm.new_department_name || ''}
                onChange={(e) =>
                  setTransferAssignmentForm({
                    ...transferAssignmentForm,
                    new_department_name: e.target.value,
                  })
                }
                placeholder="e.g. IT Department"
              />
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Transfer Date *</label>
              <Input
                type="date"
                required
                value={transferAssignmentForm.transfer_date}
                onChange={(e) =>
                  setTransferAssignmentForm({ ...transferAssignmentForm, transfer_date: e.target.value })
                }
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Condition on Transfer</label>
              <select
                value={transferAssignmentForm.condition}
                onChange={(e) =>
                  setTransferAssignmentForm({
                    ...transferAssignmentForm,
                    condition: e.target.value as AssetCondition,
                  })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="EXCELLENT">Excellent</option>
                <option value="GOOD">Good</option>
                <option value="FAIR">Fair</option>
                <option value="POOR">Poor</option>
                <option value="DAMAGED">Damaged</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Transfer Remarks</label>
            <Input
              value={transferAssignmentForm.remarks || ''}
              onChange={(e) =>
                setTransferAssignmentForm({ ...transferAssignmentForm, remarks: e.target.value })
              }
              placeholder="e.g. Reassigned to Grade 10 teacher"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowTransferAssignmentModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Transferring...' : 'Execute Transfer'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Location Create/Edit Modal */}
      <Modal
        isOpen={showLocationModal}
        onClose={() => setShowLocationModal(false)}
        title={editingLocation ? 'Edit Storage Location' : 'Add Storage Location'}
      >
        <form onSubmit={handleSaveLocation} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Location Code *</label>
              <Input
                required
                value={locationFormData.code}
                onChange={(e) => setLocationFormData({ ...locationFormData, code: e.target.value })}
                placeholder="e.g. LOC-WH-01"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Location Name *</label>
              <Input
                required
                value={locationFormData.name}
                onChange={(e) => setLocationFormData({ ...locationFormData, name: e.target.value })}
                placeholder="e.g. Central Warehouse"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Location Type *</label>
              <select
                value={locationFormData.location_type}
                onChange={(e) =>
                  setLocationFormData({
                    ...locationFormData,
                    location_type: e.target.value as InventoryLocationType,
                  })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="WAREHOUSE">Warehouse</option>
                <option value="STORE_ROOM">Store Room</option>
                <option value="LAB">Laboratory</option>
                <option value="LIBRARY_STORE">Library Store</option>
                <option value="OFFICE">Office</option>
                <option value="CLASSROOM">Classroom</option>
                <option value="SPORTS_ROOM">Sports Room</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Parent Location</label>
              <select
                value={locationFormData.parent_location_id || ''}
                onChange={(e) =>
                  setLocationFormData({
                    ...locationFormData,
                    parent_location_id: e.target.value || undefined,
                  })
                }
                className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              >
                <option value="">None (Top-Level Root)</option>
                {locations
                  .filter((loc) => !editingLocation || loc.id !== editingLocation.id)
                  .map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name} ({loc.code})
                    </option>
                  ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Building / Wing</label>
            <Input
              value={locationFormData.building_name || ''}
              onChange={(e) => setLocationFormData({ ...locationFormData, building_name: e.target.value })}
              placeholder="e.g. Science Block, Ground Floor"
            />
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Description</label>
            <textarea
              rows={2}
              value={locationFormData.description || ''}
              onChange={(e) => setLocationFormData({ ...locationFormData, description: e.target.value })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              placeholder="Access restrictions, temperature controls, etc."
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowLocationModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Location'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Vendor Create/Edit Modal */}
      <Modal
        isOpen={showVendorModal}
        onClose={() => setShowVendorModal(false)}
        title={editingVendor ? 'Edit Supplier' : 'Add Supplier / Vendor'}
      >
        <form onSubmit={handleSaveVendor} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Vendor Code *</label>
              <Input
                required
                value={vendorFormData.code}
                onChange={(e) => setVendorFormData({ ...vendorFormData, code: e.target.value })}
                placeholder="e.g. VEN-DELL"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Vendor Name *</label>
              <Input
                required
                value={vendorFormData.name}
                onChange={(e) => setVendorFormData({ ...vendorFormData, name: e.target.value })}
                placeholder="e.g. Dell Technologies India"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Contact Person</label>
              <Input
                value={vendorFormData.contact_name || ''}
                onChange={(e) => setVendorFormData({ ...vendorFormData, contact_name: e.target.value })}
                placeholder="e.g. Rajesh Kumar"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Tax / GST ID</label>
              <Input
                value={vendorFormData.tax_id || ''}
                onChange={(e) => setVendorFormData({ ...vendorFormData, tax_id: e.target.value })}
                placeholder="e.g. 29AAAAA0000A1Z5"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-ink mb-1">Email</label>
              <Input
                type="email"
                value={vendorFormData.email || ''}
                onChange={(e) => setVendorFormData({ ...vendorFormData, email: e.target.value })}
                placeholder="support@vendor.com"
              />
            </div>
            <div>
              <label className="block font-medium text-ink mb-1">Phone</label>
              <Input
                value={vendorFormData.phone || ''}
                onChange={(e) => setVendorFormData({ ...vendorFormData, phone: e.target.value })}
                placeholder="+91 98765 43210"
              />
            </div>
          </div>

          <div>
            <label className="block font-medium text-ink mb-1">Address</label>
            <textarea
              rows={2}
              value={vendorFormData.address || ''}
              onChange={(e) => setVendorFormData({ ...vendorFormData, address: e.target.value })}
              className="w-full px-3 py-2 bg-paper border border-divider rounded-md text-ink"
              placeholder="Billing & shipping address..."
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-divider">
            <Button type="button" variant="outline" onClick={() => setShowVendorModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Vendor'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmations */}
      <ConfirmDialog
        isOpen={!!deletingItemId}
        title="Delete Item from Catalog"
        message="Are you sure you want to delete this item? This action will deactivate or remove it from future transactions."
        confirmText="Delete Item"
        isDanger={true}
        isLoading={isSubmitting}
        onConfirm={handleDeleteItem}
        onClose={() => setDeletingItemId(null)}
      />

      <ConfirmDialog
        isOpen={!!deletingAssetId}
        title="Delete Physical Asset"
        message="Are you sure you want to remove this physical asset record? Ensure it is not actively assigned."
        confirmText="Delete Asset"
        isDanger={true}
        isLoading={isSubmitting}
        onConfirm={handleDeleteAsset}
        onClose={() => setDeletingAssetId(null)}
      />

      <ConfirmDialog
        isOpen={!!deletingLocationId}
        title="Delete Storage Location"
        message="Are you sure you want to remove this storage location? It must have zero remaining stock."
        confirmText="Delete Location"
        isDanger={true}
        isLoading={isSubmitting}
        onConfirm={handleDeleteLocation}
        onClose={() => setDeletingLocationId(null)}
      />

      <ConfirmDialog
        isOpen={!!deletingVendorId}
        title="Delete Vendor"
        message="Are you sure you want to remove this supplier profile?"
        confirmText="Delete Vendor"
        isDanger={true}
        isLoading={isSubmitting}
        onConfirm={handleDeleteVendor}
        onClose={() => setDeletingVendorId(null)}
      />
    </div>
  );
};
