MQTT_ENDPOINT = "localhost"   # or AWS endpoint
CA_PATH = "certs/AmazonRootCA1.pem"
CERT_PATH = "certs/device.pem.crt"
KEY_PATH = "certs/private.pem.key"
EVENTS_TOPIC = "rakan/events"
COMMANDS_TOPIC_FMT = "rakan/commands/{deviceId}"
QOS = 1
USE_TLS = true
