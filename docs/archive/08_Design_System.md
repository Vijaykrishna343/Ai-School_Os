# AI School OS — Design System Specification

## 1. Visual Philosophy
AI School OS is designed as **"The Academic Operating System"**. It rejects generic, colorful startup templates in favor of a serious, high-density, authoritative institutional environment. 

### Core Tenets
- **Institutional Authority**: The visual styling projects scholarly seriousness and operational control. Colors are restrained, opting for scholarly inks and warm neutrals rather than bright primary shades or neon badges.
- **Operational Density**: High informational density allows administrators to oversee and manage large datasets at a single glance. Compact padding and narrow margins optimize screen real estate.
- **Editorial Clarity**: Large editorial headers draw inspiration from textbook hierarchies. Important section headings use high-contrast serif typography.
- **Architectural Precision**: Visual elements use structured borders and thin separators. Layout flows follow logical data relationships (e.g. Academic Year ➔ Terms ➔ Classes ➔ Sections).

---

## 2. Color Tokens
The color palette represents a scholarly workspace—warm neutral paper surfaces, rich ink text, and deep brand highlights.

| Token | HSL / Hex | Purpose |
| :--- | :--- | :--- |
| **Paper (bg)** | `#fcf9f8` | Warm neutral primary background |
| **Surface** | `#ffffff` | Panel backgrounds, cards, registries |
| **Brand Accent** | `#1a365d` | Editorial headings, key action elements |
| **Ink (text)** | `#1c1917` | Deep near-black scholarly body text |
| **Ink Muted** | `#625b57` | Metadata, monospaced registry labels |
| **Borders** | `#e2e8f0` | Thin gridlines and container outlines |
| **Success** | `#10b981` | Restrained active/promoted statuses |
| **Warning** | `#f59e0b` | Restrained warning/on-leave statuses |
| **Danger** | `#b91c1c` | Restrained blocked/terminated statuses |

---

## 3. Typography
A dual-font system combines scholarly serif characters for editorial highlights with clean, readable sans-serif letters for operational data density.

- **Primary Serif**: `Source Serif 4`, Georgia, serif (used for editorial headers, modal headings, and page names).
- **Secondary Sans**: `Inter`, system-ui, sans-serif (used for UI elements, labels, and inputs).
- **Monospace Sans**: System monospace font (used for system codes, IDs, and statuses).

### Hierarchy Specs
- **Display Header**: `Source Serif 4`, Bold, `24px` / `text-2xl`, tracking-tight.
- **Section Heading**: `Source Serif 4`, Bold, `18px` / `text-base` or `text-sm`.
- **System Label**: `Inter`, SemiBold, `10px` / `text-[10px]`, uppercase tracking-wider.
- **Body & Table Text**: `Inter`, Regular/Medium, `12px` / `text-xs`.
- **Metadata**: Monospace, `10px` / `text-[10px]`.

---

## 4. Spacing
We use compact, structural layout rules to optimize screen scanning.

- **Layout Padding**: `p-6` (`24px`) around main page areas.
- **Widget Density**: `p-4` (`16px`) for primary container blocks.
- **Registry Rows**: Compact table rows with `py-2` (`8px`) vertical padding.
- **Gap Rules**: `gap-4` (`16px`) between filters and registry layouts.

---

## 5. Borders, Radius & Shadows
Separators and borders use clean, sharp parameters. High-elevation bubbles are avoided.

- **Border Width**: Thin `1px` gridlines for all component containers.
- **Border Radius**: Restrained `rounded-sm` (`2px`) for inputs, buttons, and badges. `rounded-none` for tables and layout panels.
- **Shadows**: Restrained `shadow-sm` on input fields/dropdowns. Floating shadows are avoided entirely.

---

## 6. Navigation System
A persistent, warm neutral sidebar organizes system functionality into a structured hierarchical rail.

### Directory Structure
1. **Overview**: Dashboard
2. **Academic Architecture**: Academics, Progression
3. **Registrar**: Student Registry, Faculty Directory, Guardian Directory
4. **Operations**: Attendance, Fees, Exams, Timetable

Active links feature an institutional left indicator bar (`border-brand-500`) with a subtle grey background toggle.

---

## 7. Page Header System
Every view starts with a structured, editorial header block:
- **Upper System Indicator**: `text-[10px] uppercase font-mono tracking-wider text-slate-500` (e.g. `OFFICE OF THE REGISTRAR`).
- **Main Editorial Title**: `text-2xl font-bold font-serif text-brand-500 mt-1`.
- **Description**: `text-xs text-slate-500 mt-1` explaining the operational view.

---

## 8. Data Table System
Registries are modeled as dense ledger sheets:
- High contrast, bold headings on a warm neutral `#fcf9f8` table header row.
- Fine light-grey row dividers (`divide-slate-150`).
- Compact table cells with monospaced roll numbers and admission numbers.
- Responsive overflow horizontal scrolling with square borders.

---

## 9. Status System
Status indicators avoid neon highlights, opting for clean fonts, thin borders, and subtle background tints:
- `ACTIVE` / `PROMOTED`: Emerald tint with deep green borders.
- `INACTIVE` / `ON_LEAVE`: Amber tint with dark yellow borders.
- `GRADUATED`: Slate grey tint with thin dark border.
- `BLOCKED` / `TERMINATED`: Rose tint with red border.

---

## 10. Forms, Modals & Drawers
- **Forms**: Clean inputs featuring monospaced labels and compact height fields (`py-2`).
- **Modals**: Standardized title bar with a neutral background, `rounded-sm` borders, and high-contrast primary actions.
- **Drawers**: Slide-over panels designed as **Student/Faculty Dossiers**—organized with thin horizontal grid lines (`IDENTITY_RECORD`, `ACADEMIC_PLACEMENT`, `LONGITUDINAL_ACADEMIC_LEDGER`).

---

## 11. Design Anti-Patterns (Avoid)
- No purple/blue gradients or glassmorphism panels.
- No bubbly `rounded-2xl` cards.
- No giant SaaS KPI card grids with colorful icons.
- No decorative illustrations without operational purpose.
- No generic, casual messaging (e.g. "Welcome back, chief!").
