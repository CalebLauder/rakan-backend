// src/components/DeviceDetail.jsx
import { useState } from "react";
import { sendCommand } from "../api/client.js";


export default function DeviceDetail({ device, onClose }) {

  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  if (!device) return null;

  const isLight = device.type === "light";
  const isThermostat = device.type === "thermostat";

  // For now, commands are just logged to the console
  async function handleCommand(action, value) {
  try {
    setBusy(true);
    setMessage(null);
    setError(null);

    const res = await sendCommand(device.id, action, value);

    // Assume backend returns something like { message: "OK" } or similar
    setMessage(res.message || "Command sent successfully.");
  } catch (err) {
    console.error("Failed to send command:", err);
    setError("Failed to send command to backend.");
  } finally {
    setBusy(false);
  }
}


  return (
    <div className="device-detail">
      <div className="device-detail-header">
        <h3>{device.name}</h3>
        <button onClick={onClose} className="detail-close-btn">
          ×
        </button>
      </div>

      <p className="device-detail-type">
        <strong>Type:</strong> {device.type}{" "}
        <span className="device-detail-separator">•</span>{" "}
        <strong>Status:</strong> {device.status}
    </p>


      {isLight && (
        <div className="device-detail-controls">
            <button
                disabled={busy}
                onClick={() =>
                    handleCommand(
                        device.status === "on" ? "turn_off" : "turn_on"
                    )
                }
            >
      {device.status === "on" ? "Turn Off" : "Turn On"}
    </button>

    <label>
      Brightness:
      <input
        type="range"
        min="0"
        max="100"
        defaultValue={device.brightness ?? 50}
        onMouseUp={(e) =>
          handleCommand("set_brightness", Number(e.target.value))
        }
      />
    </label>
  </div>
)}


      {isThermostat && (
  <div className="device-detail-controls">
    <label>
      Temperature:
      <input
        type="range"
        min="60"
        max="80"
        defaultValue={device.temperature ?? 72}
        onMouseUp={(e) =>
          handleCommand("set_temperature", Number(e.target.value))
        }
      />
    </label>

    <div className="device-detail-buttons">
      <button disabled={busy} onClick={() => handleCommand("set_mode", "cool")}>
        Cool
      </button>
      <button disabled={busy} onClick={() => handleCommand("set_mode", "heat")}>
        Heat
      </button>
      <button disabled={busy} onClick={() => handleCommand("set_mode", "off")}>
        Off
      </button>
    </div>
  </div>
)}

            {busy && <p>Sending command...</p>}
            {message && <p className="success-text">{message}</p>}
            {error && <p className="error-text">{error}</p>}

    </div>
  );
}
