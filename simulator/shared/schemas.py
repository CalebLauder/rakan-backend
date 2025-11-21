# shared/schemas.py
MOTION_SCHEMA = {
    "type": "object",
    "properties": {
        "deviceId": {"type": "string"},
        "type": {"const": "motion"},
        "motion": {"type": "boolean"},
        "timestamp": {"type": "integer"}
    },
    "required": ["deviceId", "type", "motion", "timestamp"]
}

TEMP_SCHEMA = {
    "type": "object",
    "properties": {
        "deviceId": {"type": "string"},
        "type": {"const": "temperature"},
        "value": {"type": "number"},
        "timestamp": {"type": "integer"}
    },
    "required": ["deviceId", "type", "value", "timestamp"]
}

COMMAND_SCHEMA = {
    "type": "object",
    "properties": {
        "deviceId": {"type": "string"},
        "command": {"type": "string"},
        "value": {}
    },
    "required": ["deviceId", "command"]
}
