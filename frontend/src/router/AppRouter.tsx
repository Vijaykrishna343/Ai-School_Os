import { lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '@/pages/LoginPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { AppLayout } from '@/layouts/AppLayout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PermissionRoute } from '@/components/auth/PermissionRoute';
import { useAuthStore } from '@/store/useAuthStore';

// Operational pages lazy loaded on demand
const DashboardPage = lazy(() => import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const AcademicsPage = lazy(() => import('@/pages/AcademicsPage').then((m) => ({ default: m.AcademicsPage })));
const StudentsPage = lazy(() => import('@/pages/StudentsPage').then((m) => ({ default: m.StudentsPage })));
const ParentsPage = lazy(() => import('@/pages/ParentsPage').then((m) => ({ default: m.ParentsPage })));
const TeachersPage = lazy(() => import('@/pages/TeachersPage').then((m) => ({ default: m.TeachersPage })));
const ProgressionPage = lazy(() => import('@/pages/ProgressionPage').then((m) => ({ default: m.ProgressionPage })));
const AttendancePage = lazy(() => import('@/pages/AttendancePage').then((m) => ({ default: m.AttendancePage })));
const ExamsPage = lazy(() => import('@/pages/ExamsPage').then((m) => ({ default: m.ExamsPage })));
const FeesPage = lazy(() => import('@/pages/FeesPage').then((m) => ({ default: m.FeesPage })));
const TimetablePage = lazy(() => import('@/pages/TimetablePage').then((m) => ({ default: m.TimetablePage })));
const UsersPage = lazy(() => import('@/pages/UsersPage').then((m) => ({ default: m.UsersPage })));
const RolesPage = lazy(() => import('@/pages/RolesPage').then((m) => ({ default: m.RolesPage })));
const SettingsPage = lazy(() => import('@/pages/SettingsPage').then((m) => ({ default: m.SettingsPage })));
const ImportPage = lazy(() => import('@/pages/ImportPage').then((m) => ({ default: m.ImportPage })));
const NotificationsPage = lazy(() => import('@/pages/NotificationsPage').then((m) => ({ default: m.NotificationsPage })));
const AuditLogPage = lazy(() => import('@/pages/AuditLogPage').then((m) => ({ default: m.AuditLogPage })));
const HomeworkPage = lazy(() => import('@/pages/HomeworkPage').then((m) => ({ default: m.HomeworkPage })));

const PlatformDashboard = lazy(() => import('@/pages/PlatformDashboard').then((m) => ({ default: m.PlatformDashboard })));
const SchoolsPage = lazy(() => import('@/pages/SchoolsPage').then((m) => ({ default: m.SchoolsPage })));
const SchoolSuspendedPage = lazy(() => import('@/pages/SchoolSuspendedPage').then((m) => ({ default: m.SchoolSuspendedPage })));
const PeopleAccessPage = lazy(() => import('@/pages/PeopleAccessPage').then((m) => ({ default: m.PeopleAccessPage })));
const RoleManagementPage = lazy(() => import('@/pages/RoleManagementPage').then((m) => ({ default: m.RoleManagementPage })));
const DocumentsPage = lazy(() => import('@/pages/DocumentsPage').then((m) => ({ default: m.DocumentsPage })));



export const AppRouter = () => {
  const { isAuthenticated } = useAuthStore();

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/app/dashboard" replace /> : <LoginPage />}
      />

      <Route path="/suspended" element={<SchoolSuspendedPage />} />

      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/app/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="platform" element={<PlatformDashboard />} />
        <Route path="schools" element={<SchoolsPage />} />


        <Route
          path="students"
          element={
            <PermissionRoute permission="student.view">
              <StudentsPage />
            </PermissionRoute>
          }
        />

        <Route
          path="teachers"
          element={
            <PermissionRoute permission="teacher.view">
              <TeachersPage />
            </PermissionRoute>
          }
        />

        <Route
          path="parents"
          element={
            <PermissionRoute permission="parent.view">
              <ParentsPage />
            </PermissionRoute>
          }
        />

        <Route
          path="academics"
          element={
            <PermissionRoute permission="academic_year.view">
              <AcademicsPage />
            </PermissionRoute>
          }
        />

        <Route
          path="progression"
          element={
            <PermissionRoute permission="progression_matrix.view">
              <ProgressionPage />
            </PermissionRoute>
          }
        />

        <Route
          path="attendance"
          element={
            <PermissionRoute permission="attendance.view">
              <AttendancePage />
            </PermissionRoute>
          }
        />

        <Route
          path="fees"
          element={
            <PermissionRoute permission="fees.view">
              <FeesPage />
            </PermissionRoute>
          }
        />

        <Route
          path="exams"
          element={
            <PermissionRoute permission="exam.view">
              <ExamsPage />
            </PermissionRoute>
          }
        />

        <Route
          path="timetable"
          element={
            <PermissionRoute permission="timetable.view">
              <TimetablePage />
            </PermissionRoute>
          }
        />

        <Route
          path="homework"
          element={
            <PermissionRoute permission="homework.view">
              <HomeworkPage />
            </PermissionRoute>
          }
        />

        <Route
          path="users"
          element={
            <PermissionRoute permission="user.view">
              <UsersPage />
            </PermissionRoute>
          }
        />

        <Route
          path="people"
          element={
            <PermissionRoute permission="user.view">
              <PeopleAccessPage />
            </PermissionRoute>
          }
        />


        <Route
          path="roles"
          element={
            <PermissionRoute permission="role.view">
              <RoleManagementPage />
            </PermissionRoute>
          }
        />


        <Route
          path="settings"
          element={
            <PermissionRoute permission="school.view">
              <SettingsPage />
            </PermissionRoute>
          }
        />

        <Route
          path="import"
          element={
            <PermissionRoute permission="student.create">
              <ImportPage />
            </PermissionRoute>
          }
        />

        <Route
          path="notifications"
          element={
            <PermissionRoute permission="school.view">
              <NotificationsPage />
            </PermissionRoute>
          }
        />

        <Route
          path="audit-logs"
          element={
            <PermissionRoute permission="school.view">
              <AuditLogPage />
            </PermissionRoute>
          }
        />

        <Route
          path="documents"
          element={
            <PermissionRoute permission="documents.view">
              <DocumentsPage />
            </PermissionRoute>
          }
        />
      </Route>

      <Route
        path="/"
        element={<Navigate to={isAuthenticated ? '/app/dashboard' : '/login'} replace />}
      />

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};
