import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { InventoryPage } from '@/pages/InventoryPage';
import { inventoryApi } from '@/services/api/inventoryApi';
import { teachersApi } from '@/services/api/teachersApi';
import { studentsApi } from '@/services/api/studentsApi';
import { classroomsApi } from '@/services/api/classroomsApi';
import { usersApi } from '@/services/api/usersApi';
import { useAuthStore } from '@/store/useAuthStore';
import {
  InventoryCategory,
  InventoryItem,
  InventoryLocation,
  InventoryStock,
  InventoryStockMovement,
  InventoryStockSummary,
  InventoryVendor,
  PhysicalAsset,
  AssetAssignment,
} from '@/types/models';

// Mock API modules
vi.mock('@/services/api/inventoryApi', () => ({
  inventoryApi: {
    listCategories: vi.fn(),
    getCategory: vi.fn(),
    createCategory: vi.fn(),
    updateCategory: vi.fn(),
    deleteCategory: vi.fn(),
    listLocations: vi.fn(),
    getLocation: vi.fn(),
    createLocation: vi.fn(),
    updateLocation: vi.fn(),
    deleteLocation: vi.fn(),
    listVendors: vi.fn(),
    getVendor: vi.fn(),
    createVendor: vi.fn(),
    updateVendor: vi.fn(),
    deleteVendor: vi.fn(),
    listItems: vi.fn(),
    getItem: vi.fn(),
    createItem: vi.fn(),
    updateItem: vi.fn(),
    deleteItem: vi.fn(),
    getStockSummary: vi.fn(),
    listStock: vi.fn(),
    getStock: vi.fn(),
    getStockByItem: vi.fn(),
    receiveStock: vi.fn(),
    issueStock: vi.fn(),
    returnStock: vi.fn(),
    adjustStock: vi.fn(),
    transferStock: vi.fn(),
    listMovements: vi.fn(),
    getMovement: vi.fn(),
    listAssets: vi.fn(),
    getAsset: vi.fn(),
    createAsset: vi.fn(),
    updateAsset: vi.fn(),
    deleteAsset: vi.fn(),
    retireAsset: vi.fn(),
    getAssetHistory: vi.fn(),
    listAssignments: vi.fn(),
    getAssignment: vi.fn(),
    assignAsset: vi.fn(),
    returnAsset: vi.fn(),
    transferAssignment: vi.fn(),
  },
}));

vi.mock('@/services/api/teachersApi', () => ({
  teachersApi: {
    getTeachers: vi.fn(),
  },
}));

vi.mock('@/services/api/studentsApi', () => ({
  studentsApi: {
    getStudents: vi.fn(),
  },
}));

vi.mock('@/services/api/classroomsApi', () => ({
  classroomsApi: {
    getClassrooms: vi.fn(),
  },
}));

vi.mock('@/services/api/usersApi', () => ({
  usersApi: {
    getUsers: vi.fn(),
  },
}));

// Mock Data
const mockSummary: InventoryStockSummary = {
  total_items: 24,
  total_stock_units: 350,
  total_locations: 6,
  low_stock_items_count: 2,
  out_of_stock_items_count: 1,
};

const mockCategories: InventoryCategory[] = [
  {
    id: 'cat-1',
    school_id: 'sch-1',
    name: 'IT & Electronics',
    code: 'CAT-IT',
    description: 'Hardware and peripherals',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
];

const mockLocations: InventoryLocation[] = [
  {
    id: 'loc-1',
    school_id: 'sch-1',
    name: 'Central Warehouse',
    code: 'LOC-WH-01',
    location_type: 'WAREHOUSE',
    building_name: 'Main Block',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'loc-2',
    school_id: 'sch-1',
    name: 'Science Lab Store',
    code: 'LOC-LAB-01',
    location_type: 'LAB',
    building_name: 'Science Block',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
];

const mockVendors: InventoryVendor[] = [
  {
    id: 'ven-1',
    school_id: 'sch-1',
    name: 'Dell Technologies',
    code: 'VEN-DELL',
    contact_name: 'Rajesh Kumar',
    email: 'rajesh@dell.com',
    phone: '9876543210',
    address: 'Tech Park, Bangalore',
    tax_id: '29ABCDE1234F1Z5',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
];

const mockItems: InventoryItem[] = [
  {
    id: 'itm-1',
    school_id: 'sch-1',
    category_id: 'cat-1',
    item_code: 'ITM-LAP-001',
    name: 'Dell Latitude 3420',
    description: '14-inch Core i5 Laptop',
    item_type: 'ASSET',
    unit_of_measure: 'PCS',
    track_individually: true,
    reorder_level: 5,
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    category: mockCategories[0],
  },
  {
    id: 'itm-2',
    school_id: 'sch-1',
    category_id: 'cat-1',
    item_code: 'ITM-PAP-001',
    name: 'A4 Printing Paper',
    description: '75 GSM Ream',
    item_type: 'CONSUMABLE',
    unit_of_measure: 'BOX',
    track_individually: false,
    reorder_level: 10,
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    category: mockCategories[0],
  },
];

const mockStocks: InventoryStock[] = [
  {
    id: 'stk-1',
    school_id: 'sch-1',
    item_id: 'itm-1',
    location_id: 'loc-1',
    quantity: 15,
    reserved_quantity: 0,
    unit_price: 650.0,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    item: mockItems[0],
    location: mockLocations[0],
  },
  {
    id: 'stk-2',
    school_id: 'sch-1',
    item_id: 'itm-2',
    location_id: 'loc-1',
    quantity: 3,
    reserved_quantity: 0,
    unit_price: 25.0,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    item: mockItems[1],
    location: mockLocations[0],
  },
];

const mockAssets: PhysicalAsset[] = [
  {
    id: 'ast-1',
    school_id: 'sch-1',
    item_id: 'itm-1',
    location_id: 'loc-1',
    vendor_id: 'ven-1',
    asset_tag: 'TAG-LAP-001',
    serial_number: 'SN-DELL-9492',
    model_number: 'Latitude 3420',
    status: 'AVAILABLE',
    condition: 'EXCELLENT',
    purchase_date: '2026-01-10',
    purchase_cost: 650.0,
    warranty_expiry_date: '2029-01-10',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    item: mockItems[0],
    location: mockLocations[0],
    vendor: mockVendors[0],
  },
];

const mockAssignments: AssetAssignment[] = [
  {
    id: 'asg-1',
    school_id: 'sch-1',
    asset_id: 'ast-1',
    assignment_type: 'STAFF',
    teacher_id: 'tch-1',
    assigned_date: '2026-02-01',
    expected_return_date: '2026-12-31',
    status: 'ACTIVE',
    condition_on_assignment: 'EXCELLENT',
    created_at: '2026-02-01T00:00:00Z',
    updated_at: '2026-02-01T00:00:00Z',
    asset: mockAssets[0],
  },
];

const mockMovements: InventoryStockMovement[] = [
  {
    id: 'mov-1',
    school_id: 'sch-1',
    item_id: 'itm-1',
    destination_location_id: 'loc-1',
    movement_type: 'PURCHASE_RECEIPT',
    quantity: 15,
    unit_price: 650.0,
    reference_number: 'PO-2026-001',
    movement_date: '2026-01-10T10:00:00Z',
    remarks: 'Initial stock intake',
    created_at: '2026-01-10T10:00:00Z',
    updated_at: '2026-01-10T10:00:00Z',
    item: mockItems[0],
    destination_location: mockLocations[0],
  },
];

describe('Inventory & Asset Management UI (Phase 28.4.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default auth state with full permissions
    useAuthStore.setState({
      user: {
        id: 'usr-admin',
        school_id: 'sch-1',
        email: 'admin@school.com',
        username: 'admin',
        full_name: 'Admin User',
        is_super_admin: false,
        status: 'ACTIVE',
      } as any,
      permissions: [
        'inventory.view',
        'inventory.create',
        'inventory.update',
        'inventory.delete',
        'inventory.issue',
        'inventory.transfer',
        'inventory.manage',
      ],
      roles: [{ name: 'Inventory Manager' }] as any,
      isAuthenticated: true,
    });

    // Setup default API resolutions
    (inventoryApi.getStockSummary as any).mockResolvedValue(mockSummary);
    (inventoryApi.listStock as any).mockResolvedValue({
      items: mockStocks,
      total: mockStocks.length,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });
    (inventoryApi.listCategories as any).mockResolvedValue({
      items: mockCategories,
      total: mockCategories.length,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    (inventoryApi.listLocations as any).mockResolvedValue({
      items: mockLocations,
      total: mockLocations.length,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    (inventoryApi.listVendors as any).mockResolvedValue({
      items: mockVendors,
      total: mockVendors.length,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    (inventoryApi.listItems as any).mockResolvedValue({
      items: mockItems,
      total: mockItems.length,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });
    (inventoryApi.listAssets as any).mockResolvedValue({
      items: mockAssets,
      total: mockAssets.length,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });
    (inventoryApi.listAssignments as any).mockResolvedValue({
      items: mockAssignments,
      total: mockAssignments.length,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });
    (inventoryApi.listMovements as any).mockResolvedValue({
      items: mockMovements,
      total: mockMovements.length,
      page: 1,
      page_size: 10,
      total_pages: 1,
    });

    (teachersApi.getTeachers as any).mockResolvedValue({
      items: [{ id: 'tch-1', first_name: 'John', last_name: 'Doe', teacher_code: 'TCH-01' }],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    (studentsApi.getStudents as any).mockResolvedValue({
      items: [{ id: 'stu-1', first_name: 'Alice', last_name: 'Smith', admission_number: 'ADM-001' }],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    (classroomsApi.getClassrooms as any).mockResolvedValue({
      items: [{ id: 'cls-1', name: 'Science Room 101', room_number: '101' }],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
    (usersApi.getUsers as any).mockResolvedValue({
      items: [{ id: 'usr-1', full_name: 'Staff Member', email: 'staff@school.com' }],
      total: 1,
      page: 1,
      page_size: 100,
      total_pages: 1,
    });
  });

  // ---------------------------------------------------------------------------
  // 1. Overview Dashboard
  // ---------------------------------------------------------------------------
  it('renders overview dashboard with KPI metrics and low stock alert', async () => {
    render(<InventoryPage />);

    await waitFor(() => {
      expect(screen.getByText('Catalog Items')).toBeInTheDocument();
      expect(screen.getByText('Total Units in Stock')).toBeInTheDocument();
      expect(screen.getByText('Storage Locations')).toBeInTheDocument();
      expect(screen.getByText('Low Stock Items')).toBeInTheDocument();
      expect(screen.getByText('Out of Stock')).toBeInTheDocument();
    });

    expect(screen.getByText('24')).toBeInTheDocument();
    expect(screen.getByText('350')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
    expect(screen.getByText('Low Stock Alerts')).toBeInTheDocument();
  });

  // ---------------------------------------------------------------------------
  // 2. Item Catalog Tab & CRUD
  // ---------------------------------------------------------------------------
  it('switches to item catalog, displays item list, and creates a new item', async () => {
    (inventoryApi.createItem as any).mockResolvedValue(mockItems[0]);

    render(<InventoryPage />);

    const catalogTab = screen.getByRole('button', { name: /Item Catalog/i });
    fireEvent.click(catalogTab);

    await waitFor(() => {
      expect(screen.getByText('Dell Latitude 3420')).toBeInTheDocument();
      expect(screen.getByText('A4 Printing Paper')).toBeInTheDocument();
    });

    // Click Add Item
    const addBtn = screen.getByRole('button', { name: /Add Item/i });
    fireEvent.click(addBtn);

    expect(screen.getByText('Add Item to Catalog')).toBeInTheDocument();

    // Fill form
    fireEvent.change(screen.getByPlaceholderText('e.g. ITM-LAP-001'), {
      target: { value: 'ITM-DESK-001' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g. Dell Latitude 3420'), {
      target: { value: 'Student Study Desk' },
    });

    const submitBtn = screen.getByRole('button', { name: /Save Item/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(inventoryApi.createItem).toHaveBeenCalled();
    });
  });

  // ---------------------------------------------------------------------------
  // 3. Stock Workstation Operations (Receive, Issue, Adjust, Transfer)
  // ---------------------------------------------------------------------------
  it('switches to stock tab and performs receive stock mutation', async () => {
    (inventoryApi.receiveStock as any).mockResolvedValue(mockStocks[0]);

    render(<InventoryPage />);

    const stockTab = screen.getByRole('button', { name: /Stock Levels/i });
    fireEvent.click(stockTab);

    await waitFor(() => {
      expect(screen.getByText('Available Quantity')).toBeInTheDocument();
      expect(screen.getByText('15 PCS')).toBeInTheDocument();
    });

    // Click Receive
    const receiveBtn = screen.getByRole('button', { name: /Receive/i });
    fireEvent.click(receiveBtn);

    expect(screen.getByText('Receive Stock (Purchase Receipt)')).toBeInTheDocument();

    const confirmBtn = screen.getByRole('button', { name: /Confirm Receipt/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(inventoryApi.receiveStock).toHaveBeenCalled();
    });
  });

  it('performs stock adjustment with mandatory audit reason', async () => {
    (inventoryApi.adjustStock as any).mockResolvedValue(mockStocks[0]);

    render(<InventoryPage />);

    const stockTab = screen.getByRole('button', { name: /Stock Levels/i });
    fireEvent.click(stockTab);

    await waitFor(() => {
      expect(screen.getByText('15 PCS')).toBeInTheDocument();
    });

    // Click Adjust
    const adjustBtn = screen.getByRole('button', { name: /Adjust/i });
    fireEvent.click(adjustBtn);

    expect(screen.getByText('Audit Stock Adjustment')).toBeInTheDocument();

    // Fill mandatory reason
    fireEvent.change(
      screen.getByPlaceholderText(/e\.g\. Physical inventory count reconciliation/i),
      { target: { value: 'Quarterly audit surplus count' } }
    );

    const confirmBtn = screen.getByRole('button', { name: /Confirm Adjustment/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(inventoryApi.adjustStock).toHaveBeenCalledWith(
        expect.objectContaining({
          reason: 'Quarterly audit surplus count',
          adjustment_type: 'ADD',
        })
      );
    });
  });

  it('performs stock transfer between storage locations', async () => {
    (inventoryApi.transferStock as any).mockResolvedValue(mockStocks[0]);

    render(<InventoryPage />);

    const stockTab = screen.getByRole('button', { name: /Stock Levels/i });
    fireEvent.click(stockTab);

    await waitFor(() => {
      expect(screen.getByText('15 PCS')).toBeInTheDocument();
    });

    const transferBtn = screen.getByRole('button', { name: /Transfer/i });
    fireEvent.click(transferBtn);

    expect(screen.getByText('Transfer Stock Between Locations')).toBeInTheDocument();

    const executeBtn = screen.getByRole('button', { name: /Execute Transfer/i });
    fireEvent.click(executeBtn);

    await waitFor(() => {
      expect(inventoryApi.transferStock).toHaveBeenCalled();
    });
  });

  // ---------------------------------------------------------------------------
  // 4. Physical Asset Register & Retirement
  // ---------------------------------------------------------------------------
  it('switches to physical assets tab, displays asset tag and retires an asset', async () => {
    (inventoryApi.retireAsset as any).mockResolvedValue({
      ...mockAssets[0],
      status: 'RETIRED',
    });

    render(<InventoryPage />);

    const assetTab = screen.getByRole('button', { name: /Physical Assets/i });
    fireEvent.click(assetTab);

    await waitFor(() => {
      expect(screen.getByText('TAG-LAP-001')).toBeInTheDocument();
      expect(screen.getByText('SN: SN-DELL-9492')).toBeInTheDocument();
    });

    // Click Retire Asset button
    const retireBtn = screen.getByTitle('Retire/Dispose Asset');
    fireEvent.click(retireBtn);

    expect(screen.getByText('Retire / Dispose Asset')).toBeInTheDocument();

    const confirmChangeBtn = screen.getByRole('button', { name: /Confirm Status Change/i });
    fireEvent.click(confirmChangeBtn);

    await waitFor(() => {
      expect(inventoryApi.retireAsset).toHaveBeenCalledWith(
        'ast-1',
        expect.objectContaining({ status: 'RETIRED' })
      );
    });
  });

  // ---------------------------------------------------------------------------
  // 5. Asset Assignments & Custody Workflow
  // ---------------------------------------------------------------------------
  it('switches to assignments tab and processes an asset return', async () => {
    (inventoryApi.returnAsset as any).mockResolvedValue({
      ...mockAssignments[0],
      status: 'RETURNED',
    });

    render(<InventoryPage />);

    const assignTab = screen.getByRole('button', { name: /Assignments/i });
    fireEvent.click(assignTab);

    await waitFor(() => {
      expect(screen.getByText('Custodian Target')).toBeInTheDocument();
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });

    // Click Return button
    const returnBtn = screen.getByRole('button', { name: /Return/i });
    fireEvent.click(returnBtn);

    expect(screen.getByText('Return Asset to School Custody')).toBeInTheDocument();

    const confirmReturnBtn = screen.getByRole('button', { name: /Confirm Asset Return/i });
    fireEvent.click(confirmReturnBtn);

    await waitFor(() => {
      expect(inventoryApi.returnAsset).toHaveBeenCalledWith(
        'asg-1',
        expect.objectContaining({
          condition_on_return: 'EXCELLENT',
        })
      );
    });
  });

  // ---------------------------------------------------------------------------
  // 6. Movement History (Audit Trail)
  // ---------------------------------------------------------------------------
  it('switches to movements tab and renders read-only audit log', async () => {
    render(<InventoryPage />);

    const moveTab = screen.getByRole('button', { name: /Movement History/i });
    fireEvent.click(moveTab);

    await waitFor(() => {
      expect(screen.getAllByText('Receipt').length).toBeGreaterThan(0);
      expect(screen.getByText('PO-2026-001')).toBeInTheDocument();
      expect(screen.getByText('Initial stock intake')).toBeInTheDocument();
    });
  });

  // ---------------------------------------------------------------------------
  // 7. RBAC & Security Permission Checks
  // ---------------------------------------------------------------------------
  it('hides creation, adjustment, and issue controls for read-only viewer', async () => {
    useAuthStore.setState({
      user: {
        id: 'usr-viewer',
        school_id: 'sch-1',
        email: 'viewer@school.com',
        username: 'viewer',
        full_name: 'Read Only Viewer',
        is_super_admin: false,
        status: 'ACTIVE',
      } as any,
      permissions: ['inventory.view'], // ONLY VIEW
      roles: [{ name: 'Viewer' }] as any,
      isAuthenticated: true,
    });

    render(<InventoryPage />);

    // In Dashboard quick operations
    expect(screen.queryByRole('button', { name: /Receive Stock \(Purchase\)/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Issue Consumables/i })).not.toBeInTheDocument();

    // In Catalog tab
    const catalogTab = screen.getByRole('button', { name: /Item Catalog/i });
    fireEvent.click(catalogTab);

    await waitFor(() => {
      expect(screen.getByText('Dell Latitude 3420')).toBeInTheDocument();
    });

    expect(screen.queryByRole('button', { name: /Add Item/i })).not.toBeInTheDocument();

    // In Stock tab
    const stockTab = screen.getByRole('button', { name: /Stock Levels/i });
    fireEvent.click(stockTab);

    await waitFor(() => {
      expect(screen.getByText('15 PCS')).toBeInTheDocument();
    });

    expect(screen.queryByRole('button', { name: /Receive/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Issue/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Adjust/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Transfer/i })).not.toBeInTheDocument();
  });

  // ---------------------------------------------------------------------------
  // 8. Locations & Vendors Management
  // ---------------------------------------------------------------------------
  it('switches to locations tab and creates a new location', async () => {
    (inventoryApi.createLocation as any).mockResolvedValue(mockLocations[0]);

    render(<InventoryPage />);

    const locTab = screen.getByRole('button', { name: /Locations/i });
    fireEvent.click(locTab);

    await waitFor(() => {
      expect(screen.getByText('Central Warehouse')).toBeInTheDocument();
      expect(screen.getByText('Science Lab Store')).toBeInTheDocument();
    });

    const addLocBtn = screen.getByRole('button', { name: /Add Location/i });
    fireEvent.click(addLocBtn);

    expect(screen.getByText('Add Storage Location')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText('e.g. LOC-WH-01'), {
      target: { value: 'LOC-LIB-01' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g. Central Warehouse'), {
      target: { value: 'Library Book Depot' },
    });

    const saveBtn = screen.getByRole('button', { name: /Save Location/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(inventoryApi.createLocation).toHaveBeenCalled();
    });
  });

  it('switches to vendors tab and creates a new supplier', async () => {
    (inventoryApi.createVendor as any).mockResolvedValue(mockVendors[0]);

    render(<InventoryPage />);

    const venTab = screen.getByRole('button', { name: /Vendors/i });
    fireEvent.click(venTab);

    await waitFor(() => {
      expect(screen.getByText('Dell Technologies')).toBeInTheDocument();
      expect(screen.getByText('Rajesh Kumar')).toBeInTheDocument();
    });

    const addVenBtn = screen.getByRole('button', { name: /Add Vendor/i });
    fireEvent.click(addVenBtn);

    expect(screen.getByText('Add Supplier / Vendor')).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText('e.g. VEN-DELL'), {
      target: { value: 'VEN-HP' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g. Dell Technologies India'), {
      target: { value: 'HP Enterprise Solutions' },
    });

    const saveBtn = screen.getByRole('button', { name: /Save Vendor/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(inventoryApi.createVendor).toHaveBeenCalled();
    });
  });

  // ---------------------------------------------------------------------------
  // 9. Stock Issue & Return Mutations
  // ---------------------------------------------------------------------------
  it('executes stock issue and stock return mutations', async () => {
    (inventoryApi.issueStock as any).mockResolvedValue(mockStocks[0]);
    (inventoryApi.returnStock as any).mockResolvedValue(mockStocks[0]);

    render(<InventoryPage />);

    const stockTab = screen.getByRole('button', { name: /Stock Levels/i });
    fireEvent.click(stockTab);

    await waitFor(() => {
      expect(screen.getByText('15 PCS')).toBeInTheDocument();
    });

    // Issue
    const issueBtn = screen.getByRole('button', { name: /Issue/i });
    fireEvent.click(issueBtn);

    expect(screen.getByText('Issue Stock (Consumables)')).toBeInTheDocument();
    const confirmIssueBtn = screen.getByRole('button', { name: /Confirm Issue/i });
    fireEvent.click(confirmIssueBtn);

    await waitFor(() => {
      expect(inventoryApi.issueStock).toHaveBeenCalled();
    });

    // Return
    const returnBtn = screen.getByRole('button', { name: /Return/i });
    fireEvent.click(returnBtn);

    expect(screen.getByText('Return Issued Stock to Location')).toBeInTheDocument();
    const confirmReturnBtn = screen.getByRole('button', { name: /Confirm Return/i });
    fireEvent.click(confirmReturnBtn);

    await waitFor(() => {
      expect(inventoryApi.returnStock).toHaveBeenCalled();
    });
  });
});

