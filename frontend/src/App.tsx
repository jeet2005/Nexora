import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import TabLoader from "./components/TabLoader";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const DatasetHistoryPage = lazy(() => import("./pages/DatasetHistoryPage"));
const DatasetDashboard = lazy(() => import("./pages/DatasetDashboard"));

export default function App() {
  return (
    <Suspense fallback={<TabLoader label="Loading Nexora…" />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<LandingPage />} />
          <Route path="/datasets" element={<DatasetHistoryPage />} />
          <Route path="/dataset/:datasetId" element={<DatasetDashboard />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
