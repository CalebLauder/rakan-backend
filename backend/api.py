from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import boto3
import os
import json

from backend.command_publisher import publish_command

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
STATE_TABLE = os.getenv("STATE_TABLE", "Rakan_DeviceState")
EVENT_TABLE = os.getenv("EVENT_TABLE", "Rakan_EventLogs")

dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)

# ----------------------------------------------------
# FASTAPI APP + CORS CONFIGURATION
# ----------------------------------------------------
app = FastAPI(title="Rakan Backend API")

# Allow frontend access from Vite (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------
# GET /devices
# --------------------------------
@app.get("/devices")
def get_all_devices():
    try:
        resp = dynamodb.scan(TableName=STATE_TABLE)
        devices = []

        for item in resp.get("Items", []):
            devices.append({
                "deviceId": item["deviceId"]["S"],
                "state": json.loads(item["state"]["S"]),
                "updatedAt": item["updatedAt"]["S"]
            })

        return devices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------
# GET /device/{id}
# --------------------------------
@app.get("/device/{device_id}")
def get_device(device_id: str):
    try:
        resp = dynamodb.get_item(
            TableName=STATE_TABLE,
            Key={"deviceId": {"S": device_id}}
        )

        if "Item" not in resp:
            raise HTTPException(status_code=404, detail="Device not found")

        item = resp["Item"]

        return {
            "deviceId": item["deviceId"]["S"],
            "state": json.loads(item["state"]["S"]),
            "updatedAt": item["updatedAt"]["S"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------
# GET /logs
# --------------------------------
@app.get("/logs")
def get_logs():
    try:
        resp = dynamodb.scan(TableName=EVENT_TABLE)
        logs = []

        for item in resp.get("Items", []):
            logs.append({
                "id": item["id"]["S"],
                "timestamp": item["timestamp"]["S"],
                "event": json.loads(item["event"]["S"])
            })

        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------
# POST /device/{id}/command
# --------------------------------
@app.post("/device/{device_id}/command")
def send_command(device_id: str, body: dict):
    """
    Body must contain: { "action": "...", "value": ... }
    """
    try:
        action = body.get("action")
        value = body.get("value")

        if action is None:
            raise HTTPException(status_code=400, detail="'action' is required")

        command_obj = {
            "deviceId": device_id,
            "action": action,
            "value": value,
            "reason": "manual override from API"
        }

        publish_command(device_id, command_obj)

        return {"status": "sent", "command": command_obj}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------
# LOCAL RUN
# ------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
