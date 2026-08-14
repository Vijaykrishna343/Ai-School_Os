# AI School OS — Frontend Application

Modern SaaS web application foundation for **AI School OS**, built with React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, Axios, Zustand, and Lucide React icons.

---

## Architecture Overview

- **Framework & Build Tool**: React 18 + TypeScript + Vite
- **Routing**: React Router 6 (nested routes, protected routes, permission & role guards)
- **State Management**: Zustand (`useAuthStore` for session state, `useThemeStore` for dark/light theme)
- **Data Fetching & Caching**: TanStack Query (React Query v5)
- **HTTP Client**: Centralized Axios client (`src/services/api/client.ts`) handling envelope unpacking (`{ success, message, data, errors }`), automatic 401 token refresh interceptor, and standardized error parsing.
- **Styling & Design System**: Tailwind CSS v3 with custom brand tokens, responsive grid layouts, and dark/light themes.
- **Testing**: Vitest + React Testing Library + JSDOM.

---

## Local Development & Setup

### 1. Prerequisites
- Node.js v20+
- npm v10+

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure `VITE_API_BASE_URL` points to your running FastAPI backend (e.g. `http://localhost:8000/api/v1`).

### 3. Install Dependencies
```bash
npm install
```

### 4. Start Development Server
```bash
npm run dev
```
The app will be available at `http://localhost:3000`.

---

## Available Scripts

- `npm run dev`: Start Vite development server with HMR.
- `npm run build`: Type-check TypeScript and build production bundle into `dist/`.
- `npm run preview`: Serve production build locally for testing.
- `npm run test`: Execute Vitest component test suite.

---

## Directory Structure

```
frontend/src/
├── components/
│   ├── auth/          # ProtectedRoute, PermissionRoute, RoleRoute
│   └── ui/            # Button, Input, Card, Badge, Modal, Alert, etc.
├── layouts/           # AppLayout, Sidebar, TopHeader, MobileNav
├── pages/             # LoginPage, DashboardPage, ModulePlaceholderPage, etc.
├── router/            # AppRouter configuration
├── services/
│   └── api/           # client.ts, authService.ts
├── store/             # useAuthStore.ts, useThemeStore.ts
├── test/              # Vitest setup & component test suites
├── types/             # api.ts, auth.ts
├── App.tsx
├── index.css
└── main.tsx
```
