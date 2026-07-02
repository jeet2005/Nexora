import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import TabLoader from './components/TabLoader';

const LandingPage = lazy(() => import('./pages/LandingPage'));
const DatasetHistoryPage = lazy(() => import('./pages/DatasetHistoryPage'));
const DatasetDashboard = lazy(() => import('./pages/DatasetDashboard'));
const Home = lazy(() => import('./pages/Home'));
const CyberShieldPage = lazy(() => import('./pages/CyberShieldPage'));
import { AdminLayout } from './admin/AdminLayout';
import { AdminLogin } from './admin/pages/AdminLogin';
import { Profile } from './pages/Profile';
import ProfileSettings from './pages/ProfileSettings';
import LoginPage from './pages/LoginPage';
import PublicProfilePage from './pages/PublicProfilePage';

const AdminDashboard = lazy(() => import('./admin/pages/Dashboard').then(m => ({ default: m.Dashboard })));
const AdminApiKeys = lazy(() => import('./admin/pages/ApiKeys').then(m => ({ default: m.ApiKeys })));
const AdminDatasets = lazy(() => import('./admin/pages/Datasets').then(m => ({ default: m.Datasets })));
const AdminUsers = lazy(() => import('./admin/pages/Users').then(m => ({ default: m.Users })));
const AdminContent = lazy(() => import('./admin/pages/Content').then(m => ({ default: m.Content })));
const AdminSystemHealth = lazy(() => import('./admin/pages/SystemHealth').then(m => ({ default: m.SystemHealth })));
const AdminDriftAlerts = lazy(() => import('./admin/pages/DriftAlerts').then(m => ({ default: m.DriftAlerts })));
const AdminAuditLog = lazy(() => import('./admin/pages/AuditLog').then(m => ({ default: m.AuditLog })));


export default function App() {
  return (
    <Suspense fallback={<TabLoader label="Loading Nexora…" />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<LandingPage />} />
          <Route path="/home" element={<Home />} />
          <Route path="/datasets" element={<DatasetHistoryPage />} />
          <Route path="/dataset/:datasetId" element={<DatasetDashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/profile/settings" element={<ProfileSettings />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/u/:username" element={<PublicProfilePage />} />
        </Route>
        {/* CyberShield has its own full-page dark layout */}
        <Route path="/cybershield" element={<CyberShieldPage />} />
        {/* Admin Routes */}
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="keys" element={<AdminApiKeys />} />
          <Route path="datasets" element={<AdminDatasets />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="drift" element={<AdminDriftAlerts />} />
          <Route path="health" element={<AdminSystemHealth />} />
          <Route path="content" element={<AdminContent />} />
          <Route path="audit" element={<AdminAuditLog />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
