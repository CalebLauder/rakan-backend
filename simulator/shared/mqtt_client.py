import ssl, time, logging
import paho.mqtt.client as mqtt

LOG = logging.getLogger("mqtt_client")
LOG.setLevel(logging.INFO)

class DeviceClient:
    def __init__(self, client_id, endpoint, cert=None, key=None, ca=None, use_ws=False):
        self.client_id = client_id
        self.endpoint = endpoint
        self.cert = cert
        self.key = key
        self.ca = ca

        self.client = mqtt.Client(
            client_id=client_id,
            transport="websockets" if use_ws else "tcp"
        )

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_message = None  # will be set later

        if not use_ws:
            print(f"[TLS] Loading cert={self.cert}, key={self.key}, ca={self.ca}")
            self.client.tls_set(
                ca_certs=self.ca,
                certfile=self.cert,
                keyfile=self.key,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )

    def _on_connect(self, client, userdata, flags, rc):
        print(f"[MQTT] Connected rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[MQTT] Disconnected rc={rc}")

    def _on_publish(self, client, userdata, mid):
        print(f"[MQTT] Published mid={mid}")

    def set_message_callback(self, cb):
        self.client.on_message = cb

    def connect(self, keepalive=60):
        print(f"[MQTT] Connecting to {self.endpoint}:8883 ...")
        self.client.connect(self.endpoint, 8883, keepalive)
        self.client.loop_start()
        time.sleep(0.3)

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic, payload, qos=1):
        result = self.client.publish(topic, payload, qos=qos)
        if result.rc != 0:
            print(f"[ERROR] MQTT publish failed rc={result.rc}")
        return result

    def subscribe(self, topic, qos=1):
        return self.client.subscribe(topic, qos=qos)
