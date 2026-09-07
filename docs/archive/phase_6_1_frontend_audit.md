# Phase 6.1 — Frontend Experience Audit & Inventory

This document presents the visual inventory of the AI School OS frontend (V1) and details an anti-generic-AI design audit mapping out template-like components, styling conflicts, and directions to align the product with the "Academic Operating System" vision.

---

## Part 1: Full Frontend Inventory

We have inspected the React application and compiled a complete catalog of all visible UI surfaces:

### 1. Login Page
- **Path**: [`LoginPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/LoginPage.tsx)
- **Description**: Centered white box layout against a `#fcf9f8` warm background. Features an icon, institutional title, email/password inputs, and a global error alert banner.

### 2. Dashboard / Command Center
- **Path**: [`DashboardPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/DashboardPage.tsx)
- **Description**: Features a page header, a 5-column control room metric grid (students, faculty, guardians, active classes, active sections), academic state panels, and quick links.

### 3. Sidebar (Desktop)
- **Path**: [`Sidebar.tsx`](file:///C:/Projects/school-erp/frontend/src/layouts/Sidebar.tsx)
- **Description**: Collapsible navigation rail (64px collapsed, 260px expanded). Anchors links organized into logical groups (Overview, Academic Architecture, Registrar, Operations).

### 4. Top Header
- **Path**: [`TopHeader.tsx`](file:///C:/Projects/school-erp/frontend/src/layouts/TopHeader.tsx)
- **Description**: Persistent horizontal bar (64px height) containing page titles, tenant indicator (`school_id`), dark mode toggle, and administrator user dropdown menu.

### 5. Mobile Navigation
- **Path**: [`MobileNav.tsx`](file:///C:/Projects/school-erp/frontend/src/layouts/MobileNav.tsx)
- **Description**: Slide-out menu overlay triggered from the header mobile menu button on screens < 768px. Holds mobile navigation items.

### 6. Student Registry
- **Path**: [`StudentsPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/StudentsPage.tsx#L241-L300)
- **Description**: Search filters (class, section) and a multi-column data table showing student profiles, admission numbers, statuses, and action controls.

### 7. Student Dossier Detail Drawer
- **Path**: Inline drawer render in [`StudentsPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/StudentsPage.tsx)
- **Description**: Slide-out drawer showcasing detailed student profiles, parent details, address registry, and academic progression history.

### 8. Guardian Directory
- **Path**: [`ParentsPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/ParentsPage.tsx)
- **Description**: Contains a listing of guardians/parents, primary contact fields, relationships, occupations, and quick association details.

### 9. Faculty Directory
- **Path**: [`TeachersPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/TeachersPage.tsx)
- **Description**: Faculty details table including credentials, joins/tenure records, specializations, contact cards, and class teacher assignments.

### 10. Academic Architecture
- **Path**: [`AcademicsPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/AcademicsPage.tsx)
- **Description**: Multi-tab panel separating Academic Years, Academic Terms, School Classes, and Sections, allowing administrative modifications.

### 11. Progression Workspace & Rollover Console
- **Path**: [`ProgressionPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/ProgressionPage.tsx)
- **Description**: Institutional promotion matrix configuration workspace. Contains interactive rollover preview ledgers, warnings trackers, plan verification logic, and promotional checklists.

### 12. Tables
- **Path**: [`Table.tsx`](file:///C:/Projects/school-erp/frontend/src/components/ui/Table.tsx)
- **Description**: Custom UI table skeleton and rendering layout with thin headers, bottom border-thin dividers, and row hover colors.

### 13. Forms
- **Paths**: Inline forms inside page modals in [`StudentsPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/StudentsPage.tsx), [`TeachersPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/TeachersPage.tsx), [`ParentsPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/ParentsPage.tsx), and [`AcademicsPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/AcademicsPage.tsx)
- **Description**: Structural forms containing text inputs, selection grids, state switches, and inline verification alerts.

### 14. Modals
- **Path**: [`Modal.tsx`](file:///C:/Projects/school-erp/frontend/src/components/ui/Modal.tsx)
- **Description**: Centered viewport dialog boxes with blur backdrops, modal title bars, close actions, and footer controls.

### 15. Drawers
- **Path**: [`Drawer.tsx`](file:///C:/Projects/school-erp/frontend/src/components/ui/Drawer.tsx)
- **Description**: Slide-over screen overlay sliding in from the right edge with esc-key listeners and optional actions footer.

### 16. Buttons
- **Path**: [`Button.tsx`](file:///C:/Projects/school-erp/frontend/src/components/ui/Button.tsx)
- **Description**: ForwardRef button component supporting primary, secondary, outline, ghost, and danger variations in three sizes.

### 17. Inputs
- **Path**: [`Input.tsx`](file:///C:/Projects/school-erp/frontend/src/components/ui/Input.tsx)
- **Description**: Form text fields supporting icons, labels, descriptions, validation error classes, and state-disabled behavior.

### 18. Selects
- **Paths**: Standard inputs and dropdown components in pages (e.g. filter panels)
- **Description**: Styled HTML selection drop-downs for statuses, classes, and options selection.

### 19. Badges
- **Path**: [`Badge.tsx`](file:///C:/Projects/school-erp/frontend/src/components/ui/Badge.tsx)
- **Description**: Rectangular status tags with muted color palettes (default, success, warning, error, info, neutral).

### 20. Empty States
- **Path**: [`EmptyState.tsx`](file:///C:/Projects/school-erp/frontend/src/components/ui/EmptyState.tsx)
- **Description**: Simple placeholder box showing descriptive titles, icons, and call-to-actions when lists or registries are empty.

### 21. Loading States
- **Paths**: [`LoadingState.tsx`](file:///C:/Projects/school-erp/frontend/src/components/ui/LoadingState.tsx), [`Skeleton.tsx`](file:///C:/Projects/school-erp/frontend/src/components/ui/Skeleton.tsx)
- **Description**: Skeletons and spinning indicators representing loading states for data grids and summaries.

### 22. Error States
- **Paths**: [`ErrorState.tsx`](file:///C:/Projects/school-erp/frontend/src/components/ui/ErrorState.tsx), [`Alert.tsx`](file:///C:/Projects/school-erp/frontend/src/components/ui/Alert.tsx)
- **Description**: Informational banners with error headers, diagnostic descriptions, and retry action buttons.

### 23. Forbidden (403) Page
- **Path**: [`ForbiddenPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/ForbiddenPage.tsx)
- **Description**: Shield alert graphic page representing RBAC permission blocks with return-to-dashboard routes.

### 24. Not Found (404) Page
- **Path**: [`NotFoundPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/NotFoundPage.tsx)
- **Description**: Standard 404 page indicating route mapping failures.

---

## Part 2: Anti-Generic-AI Design Audit

We evaluated every screen against modern visual design standards to identify generic SaaS patterns. The following criticisms explain where and why the current UI looks template-based, along with concrete corrective directions:

### 1. Excessive Rounded Corners on Sub-Pages & Panels
- **Problem**: Pages like [`ForbiddenPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/ForbiddenPage.tsx) and [`NotFoundPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/NotFoundPage.tsx) use `rounded-3xl` and `rounded-xl` containers.
- **Why it looks generic**: Oversized rounded corners are characteristic of modern consumer templates or generic mobile-first dashboard patterns. They strip the system of academic authority and structure.
- **Recommended Direction**: Align with the strict border radius policy of Design System V2 (maximum `rounded-sm` or `2px` for components, sharp `rounded-none` or `0px` for page panels and layout cards).

### 2. Collapsing Layout Backgrounds (Defaulting to Slate Gray)
- **Problem**: [`AppLayout.tsx`](file:///C:/Projects/school-erp/frontend/src/layouts/AppLayout.tsx) and index styles fallback to `bg-slate-50` and `text-slate-900` instead of using the custom `#fcf9f8` warm background.
- **Why it looks generic**: Slate gray backgrounds are the default Tailwind standard for generic dashboard templates. It completely undermines the scholarly, paper-like editorial aesthetic.
- **Recommended Direction**: Systematically replace `bg-slate-50` and `bg-slate-100` with the custom `bg-paper` (#fcf9f8) and custom border colors (`#e5e2da`).

### 3. Floating Card Grids & Generic KPI Summaries
- **Problem**: The Command Center dashboard uses isolated rectangular card grids with bottom color lines indicating metrics (e.g. `bg-brand-500`, `bg-emerald-600` progress indicators).
- **Why it looks generic**: Standard "KPI dashboard cards" with a big number and a tiny progress bar are highly overused in AI-generated layout templates. They lack the institutional context of a real school administration.
- **Recommended Direction**: Replace the floating card blocks with a unified grid separated by single-pixel rules. Introduce registrar-style ledgers (e.g., Daily Attendance Ledger table) directly on the command center rather than hiding everything behind routes.

### 4. Centered Login Form Card
- **Problem**: The login page features a basic white square card centered in a vast open gray canvas.
- **Why it looks generic**: The "centered box login" is the most common SaaS authentication template. It lacks visual weight and institutional authority.
- **Recommended Direction**: Shift to a split-screen layout or an editorial layout featuring a prominent institutional header, metadata tracking (such as system logs), and asymmetric, scholarly typography (Source Serif 4).

### 5. Inconsistent Typography and Hierarchy
- **Problem**: In several pages, headers toggle between `font-serif text-brand-500` and default sans-serif font styles. Section metadata is sometimes capitalized monospace, and other times plain small text.
- **Why it looks generic**: AI-generated code templates frequently apply classes like `font-bold` or `font-semibold` on sans-serif text haphazardly, resulting in a cluttered hierarchy.
- **Recommended Direction**: Enforce a strict dual-typeface rule: **Source Serif 4** for page/section titles, **Hanken Grotesk** for structured data/labels, and **Geist Mono** for metadata code blocks (e.g. ADM IDs, Hash, timestamps).

### 6. Poor Table Density
- **Problem**: The tables in Student Registry and Guardian Directories use large padding (`py-3` and `px-4`) and generic hover states (`hover:bg-slate-50`).
- **Why it looks generic**: Wide rows with lots of empty space are optimized for simple mobile apps rather than high-density registrar ledger operations.
- **Recommended Direction**: Optimize table layouts for high desktop density: reduce vertical cell padding to `py-2 px-3` and utilize a warm stone-tinted hover color (`#f2f0eb`).

### 7. Meaningless Iconography
- **Problem**: Generic icons are used for academic structures and navigation links (e.g. book icons, people icons, trending up icons).
- **Why it looks generic**: Standard Lucide icons spread throughout the page without a clear color or sizing policy look like a template.
- **Recommended Direction**: Apply a strict, restrained icon policy. Use consistent sizes (e.g., `w-4 h-4` for navigation, `w-3.5 h-3.5` for metadata). Desaturate icon colors to `#625b57` (ink-muted) so they do not compete with text.
