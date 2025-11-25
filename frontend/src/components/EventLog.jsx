// src/components/EventLog.jsx
import { useEffect, useState, useCallback } from "react";
import { mockEvents } from "../api/mockData.js";
import { fetchEvents } from "../api/client.js";

function getEventClass(type) {
  if (type === "user_command") return "event-pill-user";
  if (type === "sensor_event") return "event-pill-sensor";
  if (type === "ai_decision") return "event-pill-ai";
  if (type === "error") return "event-pill-error";
  return "event-pill-default";
}

export default function EventLog() {
  const [events, setEvents] = useState(mockEvents);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadEvents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await fetchEvents(); // <-- now an array
      setEvents(Array.isArray(data) ? data : []);

      if (data && Array.isArray(data.events)) {
        setEvents(data.events);
      } else {
        console.warn("Unexpected events response shape:", data);
      }
    } catch (err) {
      console.error("Error fetching events:", err);
      setError("Could not reach backend, showing mock events.");
      setEvents(mockEvents);
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-refresh every 4 seconds
useEffect(() => {
  loadEvents(); // initial load

  const interval = setInterval(() => {
    loadEvents();
  }, 4000); // 4 seconds

  return () => clearInterval(interval); // cleanup
}, [loadEvents]);


  if (loading && !events.length) {
    return <p>Loading events...</p>;
  }

  return (
    <div className="event-log">
      {error && <p className="error-text">{error}</p>}
      {events.map((evt) => (
        <div key={evt.id} className="event-row">
          <div className="event-header">
            <span className="event-time">{evt.timestamp}</span>
            <span className={`event-type-pill ${getEventClass(evt.type)}`}>
              {evt.type}
            </span>
          </div>

          <div className="event-body">
            <span className="event-device">{evt.deviceName}</span>
            <span className="event-message">{evt.message}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
