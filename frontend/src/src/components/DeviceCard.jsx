// src/components/DeviceCard.jsx
export default function DeviceCard({ device, onClick }) {
  const { name, type, status, brightness, temperature, lastUpdated } = device;

  function formatType(t) {
    if (t === "light") return "Light";
    if (t === "thermostat") return "Thermostat";
    if (t === "motion_sensor") return "Motion Sensor";
    return t;
  }

  return (
    <div className="device-card" onClick={onClick}>
      <div className="device-card-header">
        <span className="device-name">{name}</span>
        <span className={`device-status device-status-${status}`}>
          {String(status).toUpperCase()}
        </span>
      </div>

      <div className="device-meta">
        <span className="device-type">{formatType(type)}</span>

        {type === "light" && (
          <span className="device-detail">
            Brightness: {brightness}%
          </span>
        )}

        {type === "thermostat" && (
          <span className="device-detail">
            Temp: {temperature}°F
          </span>
        )}
      </div>

      <div className="device-footer">
        <span className="device-last-updated">
          Last updated: {lastUpdated}
        </span>
      </div>
    </div>
  );
}
