import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '@/pages/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { AcademicsPage } from '@/pages/AcademicsPage';
import { StudentsPage } from '@/pages/StudentsPage';
import { ParentsPage } from '@/pages/ParentsPage';
import { TeachersPage } from '@/pages/TeachersPage';
import { ModulePlaceholderPage } from '@/pages/ModulePlaceholderPage';
import { ProgressionPage } from '@/pages/ProgressionPage';
import { AttendancePage } from '@/pages/AttendancePage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { AppLayout } from '@/layouts/AppLayout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PermissionRoute } from '@/components/auth/PermissionRoute';
import { useAuthStore } from '@/store/useAuthStore';

export const AppRouter = () => {
  const { isAuthenticated } = useAuthStore();

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/app/dashboard" replace /> : <LoginPage />}
      />

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
            <PermissionRoute permission="progression.view">
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
            <PermissionRoute permission="fee.view">
              <ModulePlaceholderPage
                title="Fees & Payments"
                phase="Phase 5.5"
                description="Fee structures, itemized discounts, student assignments, and payment transaction collection."
              />
            </PermissionRoute>
          }
        />

        <Route
          path="exams"
          element={
            <PermissionRoute permission="exam.view">
              <ModulePlaceholderPage
                title="Exams & Report Cards"
                phase="Phase 5.4 & 5.5"
                description="Assessment schedules, student mark entries, grading scales, and report card PDF generation."
              />
            </PermissionRoute>
          }
        />

        <Route
          path="timetable"
          element={
            <PermissionRoute permission="timetable.view">
              <ModulePlaceholderPage
                title="Timetable & Slots"
                phase="Phase 5.4"
                description="Period slot allocation, classroom schedules, timetable publishing, and teacher substitutions."
              />
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
