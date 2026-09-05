import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { ToastProvider } from './context/ToastContext';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';
import Dashboard from './pages/Dashboard';
import Assets from './pages/Assets';
import AssetDetails from './pages/AssetDetails';
import DigitalTwin from './pages/DigitalTwin';
import Alerts from './pages/Alerts';
import XRay from './pages/XRay';
import FacilityMemory from './pages/FacilityMemory';
import SNSWorkbench from './pages/SNSWorkbench';
import WhatIf from './pages/WhatIf';
import IncidentGraph from './pages/IncidentGraph';

export default function App() {
  const systemStatus = {
    backend: 'healthy',
    database: 'healthy',
    kafka: 'healthy',
    xray: 'ready',
    simulator: 'ready',
    timestamp: new Date().toISOString(),
  };

  return (
    <BrowserRouter>
      <ToastProvider>
        <div className="flex min-h-screen bg-[#fafafa] text-zinc-900 font-sans antialiased selection:bg-zinc-900 selection:text-white">
          {/* Left Navigation Sidebar */}
          <Sidebar status={systemStatus} alertCount={1} />

          {/* Main Layout Area */}
          <div className="flex-1 flex flex-col min-w-0">
            <TopBar status={systemStatus} alertCount={1} />

            <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/assets" element={<Assets />} />
                <Route path="/assets/:assetId" element={<AssetDetails />} />
                <Route path="/digital-twin" element={<DigitalTwin />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/incident-graph" element={<IncidentGraph />} />
                <Route path="/facility-memory" element={<FacilityMemory />} />
                <Route path="/x-ray" element={<XRay />} />
                <Route path="/sns-workbench" element={<SNSWorkbench />} />
                <Route path="/what-if" element={<WhatIf />} />
              </Routes>
            </main>
          </div>
        </div>
      </ToastProvider>
    </BrowserRouter>
  );
}
