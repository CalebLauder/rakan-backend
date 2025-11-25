export const mockDevices = [
  {
    id: "light_livingroom_1",
    name: "Living Room Light",
    type: "light",
    status: "off",
    brightness: 0,
    lastUpdated: "2025-11-20T13:02:00Z"
  },
  {
    id: "thermostat_main",
    name: "Main Thermostat",
    type: "thermostat",
    status: "cooling",
    temperature: 72,
    lastUpdated: "2025-11-20T13:05:00Z"
  },
  {
    id: "sensor_hall_motion",
    name: "Hallway Motion Sensor",
    type: "motion_sensor",
    status: "idle",
    lastUpdated: "2025-11-20T13:10:00Z"
  }
];

export const mockEvents = [
  {
    id: "evt_001",
    timestamp: "2025-11-20T13:02:10Z",
    deviceId: "light_livingroom_1",
    deviceName: "Living Room Light",
    type: "ai_decision",
    message: "LAM turned on the light due to detected motion."
  },
  {
    id: "evt_002",
    timestamp: "2025-11-20T13:03:15Z",
    deviceId: "thermostat_main",
    deviceName: "Main Thermostat",
    type: "user_command",
    message: "User set temperature to 72°F."
  },
  {
    id: "evt_003",
    timestamp: "2025-11-20T13:04:30Z",
    deviceId: "sensor_hall_motion",
    deviceName: "Hallway Motion Sensor",
    type: "sensor_event",
    message: "Motion detected in hallway."
  }
];
