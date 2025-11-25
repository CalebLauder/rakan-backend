// src/api/client.js

// Vite exposes environment variables that start with VITE_
// We'll configure VITE_API_BASE_URL in a .env file.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:3000";

export async function fetchDevices() {
  const res = await fetch(`${BASE_URL}/api/devices`);
  if (!res.ok) {
    throw new Error(`Failed to fetch devices: ${res.status}`);
  }
  return res.json(); // expected shape: { devices: [...] }
}

export async function fetchEvents() {
  const res = await fetch(`${BASE_URL}/api/events`);
  if (!res.ok) {
    throw new Error(`Failed to fetch events: ${res.status}`);
  }
  return res.json(); // expected shape: { events: [...] }
}

export async function sendCommand(deviceId, action, value) {
  const res = await fetch(`${BASE_URL}/api/control`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ deviceId, action, value })
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Failed to send command: ${res.status}`);
  }

  return res.json(); // whatever backend returns (e.g. { message: "OK" })
}
