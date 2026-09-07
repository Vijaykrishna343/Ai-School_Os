# Phase 6.1 — Screen-by-Screen Redesign Plan

This document establishes the concrete redesign roadmap for each screen of the AI School OS frontend, guiding the implementation of Design System V2 in Phase 6.2.

---

## 1. Login Page Redesign
* **Current Page**: [`LoginPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/LoginPage.tsx)
* **Redesign Actions**:
  - Replace the floating white card layout with a scholarly split-screen or a centered archival document layout.
  - Apply the parchment background `#fcf9f8` to the entire screen.
  - Set the login header title in **Source Serif 4** with an elegant under-line.
  - Modify inputs to use the new editability policy: a light `#f2f0eb` cream background that transitions to a white background on active focus.
  - Align security notices and errors at the bottom of the form in desaturated ink-muted boxes.

## 2. Administrative Command Center (Dashboard)
* **Current Page**: [`DashboardPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/DashboardPage.tsx)
* **Redesign Actions**:
  - Dismantle isolated floating card grids. Combine summary counts into a unified metric ledger bar bounded by a 1px border.
  - Place a **Daily Attendance Ledger** table directly on the command center as a primary component, presenting grade-level rates (Grade 9-12 enrollments and absenteeism metrics).
  - Clean up quick links by removing large card borders. Format links as a clean, list-style administrative docket.
  - Apply monospaced `Geist Mono` font formatting on school ID codes, dates, and database reference tags.

## 3. Student Registry
* **Current Page**: [`StudentsPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/StudentsPage.tsx)
* **Redesign Actions**:
  - Transition the primary data table to use thin vertical gridlines (`#e5e2da` borders) and compact cells (`py-2 px-3`) to increase visual density.
  - Enforce status badges to follow the rectangular, low-saturation success/info scheme.
  - Clean up the query toolbar: make select inputs flat with thin dividers, and align filter buttons to sit in a single registrar-style command strip.

## 4. Student Dossier Detail Drawer
* **Current Page**: Inline Drawer inside [`StudentsPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/StudentsPage.tsx)
* **Redesign Actions**:
  - Restructure profile data using an asymmetrical layout grid (left column for personal metadata, right column for enrollment history).
  - Format the student enrollment history ledger as a compact table showing progression rule statuses.
  - Apply desaturated headers and format contact numbers in `Geist Mono`.

## 5. Guardian Directory
* **Current Page**: [`ParentsPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/ParentsPage.tsx)
* **Redesign Actions**:
  - Redesign parent cards and directories into a ledger-like table showing relationship matrices (Father, Mother, Guardian associations).
  - Implement clean actions links instead of bubbly buttons.

## 6. Faculty Directory
* **Current Page**: [`TeachersPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/TeachersPage.tsx)
* **Redesign Actions**:
  - Show teacher credentials, qualifications, joining date, and specialization codes in a compact grid structure.
  - Format status tags to be small, rectangular, and neutral.

## 7. Academic Architecture Page
* **Current Page**: [`AcademicsPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/AcademicsPage.tsx)
* **Redesign Actions**:
  - Redesign year, term, class, and section panels to display as a unified scholastic directory.
  - Transition form tabs from rounded bubbles to flat, underline-based tab selections.
  - Format active items (e.g. current academic year) in success badges, and future items in info badges.

## 8. Progression Workspace & Rollover Console
* **Current Page**: [`ProgressionPage.tsx`](file:///C:/Projects/school-erp/frontend/src/pages/ProgressionPage.tsx)
* **Redesign Actions**:
  - Simplify matrix rules mapping display: use flat lines instead of cards.
  - Format dry-run preview outcome codes (PROMOTED, RETAINED, GRADUATED, BLOCKED) as desaturated badges.
  - Style the plan hash validation block in `Geist Mono` inside a secure, flat verification card with clear instructions.
  - Render warnings and conflict diagnostics in desaturated alert panels.

## 9. Layout (Sidebar & Top Header)
* **Current layouts**: [`Sidebar.tsx`](file:///C:/Projects/school-erp/frontend/src/layouts/Sidebar.tsx), [`TopHeader.tsx`](file:///C:/Projects/school-erp/frontend/src/layouts/TopHeader.tsx), [`MobileNav.tsx`](file:///C:/Projects/school-erp/frontend/src/layouts/MobileNav.tsx)
* **Redesign Actions**:
  - Change main workspace wrapper background in [`AppLayout.tsx`](file:///C:/Projects/school-erp/frontend/src/layouts/AppLayout.tsx) from `bg-slate-50` to the paper background `#fcf9f8`.
  - Shift sidebar background to `#f4f1ef` to provide a subtle, physical contrast.
  - Replace navigation rounded selections with flat links. Place a 2px left brand-line to indicate the active navigation state.
  - In `MobileNav`, replace `rounded-xl` and `rounded-3xl` classes with `rounded-sm` to maintain system design coherence.
