# Phase 6.1 — Design System V2 Specs

This document specifies the design system v2 tokens, layout guidelines, and component patterns for the AI School OS frontend.

---

## 1. Color Palette & Tokens

The evolved color palette is built on the metaphor of **"Ink on Paper"**, representing traditional institutional records:

| Token | CSS / Tailwind Class | Hex Value | Purpose |
| :--- | :--- | :--- | :--- |
| **Paper (Base)** | `bg-paper` | `#fcf9f8` | Core background for all page layouts |
| **Paper-Dim** | `bg-[#f4f1ef]` | `#f4f1ef` | Sidebar background & panel section fills |
| **Ink (Default)** | `text-ink` | `#1c1917` | Standard readable text |
| **Ink-Muted** | `text-ink-muted` | `#625b57` | Labels, details, desaturated metadata |
| **Brand (Primary)** | `text-brand-500` / `bg-brand-500` | `#1a365d` | Editorial headings and primary command accents |
| **Border-Thin** | `border-slate-200` | `#e2e8f0` | General divider line color |
| **Border-Warm** | `border-[#e5e2da]` | `#e5e2da` | Table dividers and structural outlines |

### Status Alerts & Accents (Desaturated Tones)
* **Success**: `text-emerald-800 bg-emerald-50/40 border-emerald-200/60` (active/promoted)
* **Info**: `text-sky-800 bg-sky-50/40 border-sky-200/60` (upcoming/neutral highlight)
* **Warning**: `text-amber-800 bg-amber-50/40 border-amber-200/60` (retained/warnings check)
* **Danger**: `text-red-800 bg-red-50/40 border-red-200/60` (blocked/deleted)

---

## 2. Typography

We enforce a strict dual-typeface font mapping:

```
  SCHOLARLY HEADINGS (Source Serif 4)
  ➔ Page Titles, Section Headers, Login Title

  FUNCTIONAL DATA (Hanken Grotesk / Inter)
  ➔ Table Cells, Form Input Text, Body Paragraphs

  SYSTEM METADATA (Geist Mono)
  ➔ ID Codes, Hashes, Dates, Status Log Codes
```

### Typographic Styles
* **Page Title (Display)**: `font-serif text-3xl font-bold tracking-tight text-brand-500`
* **Section Title**: `font-serif text-xl font-semibold text-brand-500`
* **Table Header Label**: `font-sans text-[10px] font-bold uppercase tracking-wider text-ink-muted`
* **Body / Cell Text**: `font-sans text-xs text-ink`
* **System Metadata / Codes**: `font-mono text-[11px] text-ink-muted`

---

## 3. Shape & Depth Policy

### Radius Policy
* **General components** (buttons, inputs): strictly `rounded-sm` (2px) or `rounded` (3px/4px).
* **Large layout panels** (modals, detail boxes, card grids): strictly `rounded-none` (0px).
* **Pill badges/large rounded corners** (e.g. `rounded-3xl`): strictly prohibited.

### Elevation & Shadow Policy
* No generic box shadows or drop shadows (`shadow-md`, `shadow-lg`).
* Flat layout sheets separated by 1px solid outlines (`#e5e2da` / `#e2e8f0`).
* Floating layers (menus, dropdowns, modals): use a crisp, tight 1px outline with a minimal 2px shadow (`shadow-[0_2px_2px_rgba(0,0,0,0.08)]`).

---

## 4. Component Visual Specifications

### 4.1 Buttons
* **Primary**: Filled rectangular background in brand blue (`#1a365d`), text is white, corners are `rounded-sm` (2px).
* **Secondary / Outline**: 1px border (`#e2e8f0`), text is dark, background is transparent, hovering shifts background color slightly to `#f2f0eb`.
* **Danger**: Filled red background, desaturated to maintain the scholarly, low-saturation tone.

### 4.2 Inputs & Selects
* Full border (`border-slate-300`) or flat bottom-border only.
* Editability state: Input boxes have a soft cream fill `#f2f0eb` to designate them as fields, changing to a clean white fill on active focus with a bold `border-brand-500`.

### 4.3 Data Tables
* Flat layout, separated by single-pixel horizontal borders (`#e5e2da`).
* High-density vertical cell padding (`py-2 px-3`).
* Header cells have a subtle background tint (`bg-paper-dim` or `#f4f1ef`) and use `label-caps` (uppercase tracker).

### 4.4 Drawer and Modal Layouts
* Drawers slide in from the right edge with a clean vertical divider line and no drop shadow.
* Modal heads use the warm paper background with a clear, thin dividing line.

### 4.5 Navigation Rail & Header Bar
* Sidebar uses the warm dim background `#f4f1ef` to stand out from the page.
* Nav links are flat (no card background); active link indicated by a vertical 2px colored brand-line on the left border.

---

## 5. Feedbacks & Layout States

### 5.1 Empty States
* Minimalist layout: desaturated ink-muted icon, small sans title, and a simple secondary outline button.

### 5.2 Loading / Skeleton Screens
* Flat skeleton layouts matching the exact layout of the target table or card grid. No flashing neon gradients; use slow fade loops.

### 5.3 Error & Warning Banners
* Desaturated banner cards (muted red background `#fff5f5`, thin red border `#ffc1c1`) with code details printed in `Geist Mono`.
