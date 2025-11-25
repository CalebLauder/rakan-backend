// src/App.jsx
import { useState } from "react";
import DashboardLayout from "./layouts/DashboardLayout.jsx";
import DeviceList from "./components/DeviceList.jsx";
import EventLog from "./components/EventLog.jsx";
import DeviceDetail from "./components/DeviceDetail.jsx";


export default function App() {
const [selectedDevice, setSelectedDevice] = useState(null);
  return (
    <DashboardLayout>
      <header className="app-header">
        <div className="app-header-main">
          <div>
            <h1>Rakan Smart Home Dashboard</h1>
            <p>Monitor devices, view AI decisions, and send commands.</p>
          </div>
          <div className="app-header-badges">
            <span className="badge badge-ai">AI: Active</span>
            <span className="badge badge-mode">Mode: Home</span>
          </div>
        </div>
      </header>

      <div className="dashboard-content">
        <section className="devices-panel">
        <h2>Devices</h2>
        <DeviceList onSelectDevice={setSelectedDevice} />
      </section>



        <section className="events-panel">
          <h2>Activity Log</h2>
          <EventLog />

          {selectedDevice && (
            <DeviceDetail
              device={selectedDevice}
              onClose={() => setSelectedDevice(null)}
            />
          )}
        </section>


      </div>
    </DashboardLayout>
  );
}
