import { apiClient } from './client';
import {
  AssetAssignment,
  AssetAssignmentCreate,
  AssetAssignmentReturnRequest,
  AssetAssignmentStatus,
  AssetAssignmentTransferRequest,
  AssetAssignmentType,
  AssetCondition,
  AssetStatus,
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
  PaginatedResponse,
  PhysicalAsset,
  PhysicalAssetCreate,
  PhysicalAssetRetireRequest,
  PhysicalAssetUpdate,
  StockAdjustmentRequest,
  StockIssueRequest,
  StockReceiveRequest,
  StockReturnRequest,
  StockTransferRequest,
} from '@/types/models';

export interface InventoryCategoryFilterParams {
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface InventoryLocationFilterParams {
  location_type?: InventoryLocationType;
  parent_location_id?: string;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface InventoryVendorFilterParams {
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface InventoryItemFilterParams {
  category_id?: string;
  item_type?: InventoryItemType;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface InventoryStockFilterParams {
  item_id?: string;
  location_id?: string;
  category_id?: string;
  low_stock?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface InventoryMovementFilterParams {
  item_id?: string;
  source_location_id?: string;
  destination_location_id?: string;
  movement_type?: InventoryStockMovementType;
  reference_number?: string;
  page?: number;
  page_size?: number;
}

export interface InventoryAssetFilterParams {
  item_id?: string;
  location_id?: string;
  vendor_id?: string;
  status?: AssetStatus;
  condition?: AssetCondition;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface InventoryAssignmentFilterParams {
  asset_id?: string;
  assignment_type?: AssetAssignmentType;
  status?: AssetAssignmentStatus;
  teacher_id?: string;
  student_id?: string;
  classroom_id?: string;
  page?: number;
  page_size?: number;
}

export const inventoryApi = {
  // ---------------------------------------------------------------------------
  // 1. Categories
  // ---------------------------------------------------------------------------
  listCategories: async (
    params?: InventoryCategoryFilterParams
  ): Promise<PaginatedResponse<InventoryCategory>> => {
    const response = await apiClient.get<PaginatedResponse<InventoryCategory>>(
      '/inventory/categories',
      { params }
    );
    return response.data;
  },

  getCategory: async (categoryId: string): Promise<InventoryCategory> => {
    const response = await apiClient.get<InventoryCategory>(
      `/inventory/categories/${categoryId}`
    );
    return response.data;
  },

  createCategory: async (
    payload: InventoryCategoryCreate
  ): Promise<InventoryCategory> => {
    const response = await apiClient.post<InventoryCategory>(
      '/inventory/categories',
      payload
    );
    return response.data;
  },

  updateCategory: async (
    categoryId: string,
    payload: InventoryCategoryUpdate
  ): Promise<InventoryCategory> => {
    const response = await apiClient.put<InventoryCategory>(
      `/inventory/categories/${categoryId}`,
      payload
    );
    return response.data;
  },

  deleteCategory: async (categoryId: string): Promise<void> => {
    await apiClient.delete(`/inventory/categories/${categoryId}`);
  },

  // ---------------------------------------------------------------------------
  // 2. Locations
  // ---------------------------------------------------------------------------
  listLocations: async (
    params?: InventoryLocationFilterParams
  ): Promise<PaginatedResponse<InventoryLocation>> => {
    const response = await apiClient.get<PaginatedResponse<InventoryLocation>>(
      '/inventory/locations',
      { params }
    );
    return response.data;
  },

  getLocation: async (locationId: string): Promise<InventoryLocation> => {
    const response = await apiClient.get<InventoryLocation>(
      `/inventory/locations/${locationId}`
    );
    return response.data;
  },

  createLocation: async (
    payload: InventoryLocationCreate
  ): Promise<InventoryLocation> => {
    const response = await apiClient.post<InventoryLocation>(
      '/inventory/locations',
      payload
    );
    return response.data;
  },

  updateLocation: async (
    locationId: string,
    payload: InventoryLocationUpdate
  ): Promise<InventoryLocation> => {
    const response = await apiClient.put<InventoryLocation>(
      `/inventory/locations/${locationId}`,
      payload
    );
    return response.data;
  },

  deleteLocation: async (locationId: string): Promise<void> => {
    await apiClient.delete(`/inventory/locations/${locationId}`);
  },

  // ---------------------------------------------------------------------------
  // 3. Vendors
  // ---------------------------------------------------------------------------
  listVendors: async (
    params?: InventoryVendorFilterParams
  ): Promise<PaginatedResponse<InventoryVendor>> => {
    const response = await apiClient.get<PaginatedResponse<InventoryVendor>>(
      '/inventory/vendors',
      { params }
    );
    return response.data;
  },

  getVendor: async (vendorId: string): Promise<InventoryVendor> => {
    const response = await apiClient.get<InventoryVendor>(
      `/inventory/vendors/${vendorId}`
    );
    return response.data;
  },

  createVendor: async (
    payload: InventoryVendorCreate
  ): Promise<InventoryVendor> => {
    const response = await apiClient.post<InventoryVendor>(
      '/inventory/vendors',
      payload
    );
    return response.data;
  },

  updateVendor: async (
    vendorId: string,
    payload: InventoryVendorUpdate
  ): Promise<InventoryVendor> => {
    const response = await apiClient.put<InventoryVendor>(
      `/inventory/vendors/${vendorId}`,
      payload
    );
    return response.data;
  },

  deleteVendor: async (vendorId: string): Promise<void> => {
    await apiClient.delete(`/inventory/vendors/${vendorId}`);
  },

  // ---------------------------------------------------------------------------
  // 4. Items (Catalog)
  // ---------------------------------------------------------------------------
  listItems: async (
    params?: InventoryItemFilterParams
  ): Promise<PaginatedResponse<InventoryItem>> => {
    const response = await apiClient.get<PaginatedResponse<InventoryItem>>(
      '/inventory/items',
      { params }
    );
    return response.data;
  },

  getItem: async (itemId: string): Promise<InventoryItem> => {
    const response = await apiClient.get<InventoryItem>(
      `/inventory/items/${itemId}`
    );
    return response.data;
  },

  createItem: async (
    payload: InventoryItemCreate
  ): Promise<InventoryItem> => {
    const response = await apiClient.post<InventoryItem>(
      '/inventory/items',
      payload
    );
    return response.data;
  },

  updateItem: async (
    itemId: string,
    payload: InventoryItemUpdate
  ): Promise<InventoryItem> => {
    const response = await apiClient.put<InventoryItem>(
      `/inventory/items/${itemId}`,
      payload
    );
    return response.data;
  },

  deleteItem: async (itemId: string): Promise<void> => {
    await apiClient.delete(`/inventory/items/${itemId}`);
  },

  // ---------------------------------------------------------------------------
  // 5. Stock Visibility & Operations
  // ---------------------------------------------------------------------------
  getStockSummary: async (): Promise<InventoryStockSummary> => {
    const response = await apiClient.get<InventoryStockSummary>(
      '/inventory/stock/summary'
    );
    return response.data;
  },

  listStock: async (
    params?: InventoryStockFilterParams
  ): Promise<PaginatedResponse<InventoryStock>> => {
    const response = await apiClient.get<PaginatedResponse<InventoryStock>>(
      '/inventory/stock',
      { params }
    );
    return response.data;
  },

  getStock: async (stockId: string): Promise<InventoryStock> => {
    const response = await apiClient.get<InventoryStock>(
      `/inventory/stock/${stockId}`
    );
    return response.data;
  },

  getStockByItem: async (itemId: string): Promise<InventoryStock[]> => {
    const response = await apiClient.get<InventoryStock[]>(
      `/inventory/stock/items/${itemId}`
    );
    return response.data;
  },

  receiveStock: async (payload: StockReceiveRequest): Promise<InventoryStock> => {
    const response = await apiClient.post<InventoryStock>(
      '/inventory/stock/receive',
      payload
    );
    return response.data;
  },

  issueStock: async (payload: StockIssueRequest): Promise<InventoryStock> => {
    const response = await apiClient.post<InventoryStock>(
      '/inventory/stock/issue',
      payload
    );
    return response.data;
  },

  returnStock: async (payload: StockReturnRequest): Promise<InventoryStock> => {
    const response = await apiClient.post<InventoryStock>(
      '/inventory/stock/return',
      payload
    );
    return response.data;
  },

  adjustStock: async (payload: StockAdjustmentRequest): Promise<InventoryStock> => {
    const response = await apiClient.post<InventoryStock>(
      '/inventory/stock/adjust',
      payload
    );
    return response.data;
  },

  transferStock: async (payload: StockTransferRequest): Promise<InventoryStock> => {
    const response = await apiClient.post<InventoryStock>(
      '/inventory/stock/transfer',
      payload
    );
    return response.data;
  },

  // ---------------------------------------------------------------------------
  // 6. Movement History
  // ---------------------------------------------------------------------------
  listMovements: async (
    params?: InventoryMovementFilterParams
  ): Promise<PaginatedResponse<InventoryStockMovement>> => {
    const response = await apiClient.get<PaginatedResponse<InventoryStockMovement>>(
      '/inventory/movements',
      { params }
    );
    return response.data;
  },

  getMovement: async (movementId: string): Promise<InventoryStockMovement> => {
    const response = await apiClient.get<InventoryStockMovement>(
      `/inventory/movements/${movementId}`
    );
    return response.data;
  },

  // ---------------------------------------------------------------------------
  // 7. Physical Assets
  // ---------------------------------------------------------------------------
  listAssets: async (
    params?: InventoryAssetFilterParams
  ): Promise<PaginatedResponse<PhysicalAsset>> => {
    const response = await apiClient.get<PaginatedResponse<PhysicalAsset>>(
      '/inventory/assets',
      { params }
    );
    return response.data;
  },

  getAsset: async (assetId: string): Promise<PhysicalAsset> => {
    const response = await apiClient.get<PhysicalAsset>(
      `/inventory/assets/${assetId}`
    );
    return response.data;
  },

  createAsset: async (payload: PhysicalAssetCreate): Promise<PhysicalAsset> => {
    const response = await apiClient.post<PhysicalAsset>(
      '/inventory/assets',
      payload
    );
    return response.data;
  },

  updateAsset: async (
    assetId: string,
    payload: PhysicalAssetUpdate
  ): Promise<PhysicalAsset> => {
    const response = await apiClient.put<PhysicalAsset>(
      `/inventory/assets/${assetId}`,
      payload
    );
    return response.data;
  },

  deleteAsset: async (assetId: string): Promise<void> => {
    await apiClient.delete(`/inventory/assets/${assetId}`);
  },

  retireAsset: async (
    assetId: string,
    payload: PhysicalAssetRetireRequest
  ): Promise<PhysicalAsset> => {
    const response = await apiClient.post<PhysicalAsset>(
      `/inventory/assets/${assetId}/retire`,
      payload
    );
    return response.data;
  },

  getAssetHistory: async (assetId: string): Promise<AssetAssignment[]> => {
    const response = await apiClient.get<AssetAssignment[]>(
      `/inventory/assets/${assetId}/history`
    );
    return response.data;
  },

  // ---------------------------------------------------------------------------
  // 8. Asset Assignments
  // ---------------------------------------------------------------------------
  listAssignments: async (
    params?: InventoryAssignmentFilterParams
  ): Promise<PaginatedResponse<AssetAssignment>> => {
    const response = await apiClient.get<PaginatedResponse<AssetAssignment>>(
      '/inventory/assignments',
      { params }
    );
    return response.data;
  },

  getAssignment: async (assignmentId: string): Promise<AssetAssignment> => {
    const response = await apiClient.get<AssetAssignment>(
      `/inventory/assignments/${assignmentId}`
    );
    return response.data;
  },

  assignAsset: async (
    payload: AssetAssignmentCreate
  ): Promise<AssetAssignment> => {
    const response = await apiClient.post<AssetAssignment>(
      '/inventory/assignments',
      payload
    );
    return response.data;
  },

  returnAsset: async (
    assignmentId: string,
    payload: AssetAssignmentReturnRequest
  ): Promise<AssetAssignment> => {
    const response = await apiClient.post<AssetAssignment>(
      `/inventory/assignments/${assignmentId}/return`,
      payload
    );
    return response.data;
  },

  transferAssignment: async (
    assignmentId: string,
    payload: AssetAssignmentTransferRequest
  ): Promise<AssetAssignment> => {
    const response = await apiClient.post<AssetAssignment>(
      `/inventory/assignments/${assignmentId}/transfer`,
      payload
    );
    return response.data;
  },
};
