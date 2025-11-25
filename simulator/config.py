import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MQTT_ENDPOINT = "a2cu3qgpy7qzdx-ats.iot.us-east-1.amazonaws.com"

CA_PATH   = os.path.join(BASE_DIR, "certs", "AmazonRootCA1.pem")
CERT_PATH = os.path.join(BASE_DIR, "certs", "dev-device.pem.crt")
KEY_PATH  = os.path.join(BASE_DIR, "certs", "dev-private.pem.key")

EVENTS_TOPIC = "rakan/events"
COMMANDS_TOPIC_FMT = "rakan/commands/{deviceId}"

QOS = 1
USE_TLS = True
