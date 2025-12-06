Rakan Backend

Backend services for the Rakan IoT Automation System.
This repo contains:

AWS Lambda (Event Processor)

LAMDecisionEngine (AI logic)

MQTT device simulators

DynamoDB integration

Optional FastAPI backend for frontend access

Project Overview

The backend processes IoT device events sent through AWS IoT Core, runs automation logic, and returns commands back to devices. Device state and event history are stored in DynamoDB.

Folder Structure
rakan-backend/
│
├── event_processor/
│   ├── event_processor.py        # Main Lambda logic
│   └── command_publisher.py      # Publishes commands back to IoT Core
│
├── simulator/
│   ├── motion_sensor.py
│   ├── temperature_sensor.py
│   ├── base_simulator.py
│   └── shared/
│       └── mqtt_client.py
│
├── api/                          # Optional FastAPI service
├── certs/                        # IoT device certificates
└── README.md

AWS Resources Used

AWS IoT Core
Receives MQTT events from devices and forwards them to Lambda.

AWS Lambda (EventProcessor)

Logs events to Rakan_EventLogs

Calls LAMDecisionEngine

Publishes commands to:

rakan/commands/{deviceId}


Updates Rakan_DeviceState

AWS Lambda (LAMDecisionEngine)
Simple rules/AI logic that returns a decision JSON object.

DynamoDB

Rakan_EventLogs → event history

Rakan_DeviceState → latest state per device

Environment Variables (EventProcessor Lambda)
Name	Example Value
EVENT_TABLE	Rakan_EventLogs
STATE_TABLE	Rakan_DeviceState
LAM_FUNCTION_NAME	LAMDecisionEngine
COMMAND_TOPIC_FMT	rakan/commands/{deviceId}
Running the Simulators

Install dependencies:

pip install -r requirements.txt


Activate virtual environment (if using one):

source venv/bin/activate


Run motion sensor:

python -m simulator.motion_sensor


Run temperature sensor:

python -m simulator.temperature_sensor


Simulators publish MQTT events to:

rakan/events

and listen for commands on:

rakan/commands/{deviceId}

Testing with MQTT Client

In AWS IoT Console → MQTT Test Client:

Subscribe to:

rakan/events/#
rakan/commands/#


You should see sensor events and Lambda-generated commands.

FastAPI (Optional)

Provides endpoints:

/devices

/logs

/device/{id}

/device/{id}/command

Used by frontend for display + control.

License

MIT License
