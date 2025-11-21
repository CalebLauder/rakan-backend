EVENT FORMAT:

{
  "deviceId": "device1",
  "type": "motion",
  "value": true,
  "timestamp": "2025-11-19T12:00:00Z"
}
COMMAND FORMAT:

{
  "deviceId": "device1",
  "action": "switch",
  "value": true
}
MQTT Topics:

rakan/events
rakan/commands/<deviceId>
