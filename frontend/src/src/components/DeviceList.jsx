// src/components/DeviceList.jsx
import { useEffect, useState, useCallback } from "react";
import { mockDevices } from "../api/mockData.js";
import { fetchDevices } from "../api/client.js";
import DeviceCard from "./DeviceCard.jsx";

export default function DeviceList({ onSelectDevice }) {
  const [devices, setDevices] = useState(mockDevices);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadDevices = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await fetchDevices(); // { devices: [...] }
      if (data && Array.isArray(data.devices)) {
        setDevices(data.devices);
      } else {
        // backend returned something unexpected, keep old devices
        console.warn("Unexpected devices response shape:", data);
      }
    } catch (err) {
      console.error("Error fetching devices:", err);
      setError("Could not reach backend, showing mock devices.");
      setDevices(mockDevices);
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-refresh every 5 seconds
useEffect(() => {
  loadDevices();  // initial load

  const interval = setInterval(() => {
    loadDevices();
  }, 5000); // 5 seconds

  return () => clearInterval(interval); // cleanup on unmount
}, [loadDevices]);


  if (loading && !devices.length) {
    return <p>Loading devices...</p>;
  }

  return (
    <>
      {error && <p className="error-text">{error}</p>}
      <div className="device-list">
        {devices.map((device) => (
          <DeviceCard
            key={device.id}
            device={device}
            onClick={() => {
              if (onSelectDevice) onSelectDevice(device);
            }}
          />
        ))}
      </div>
    </>
  );
}
