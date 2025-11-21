# simulator/shared/mqtt_client.py
import ssl, time, logging
import paho.mqtt.client as mqtt

LOG = logging.getLogger("mqtt_client")
LOG.setLevel(logging.INFO)

class DeviceClient:
    def __init__(self, client_id, endpoint, cert=None, key=None, ca=None, use_ws=False):
        self.client_id = client_id
        self.endpoint = endpoint
        self.cert = cert; self.key = key; self.ca = ca
        self.client = mqtt.Client(client_id=client_id, transport="websockets" if use_ws else "tcp")
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_message = None
        if not use_ws:
            self.client.tls_set(ca_certs=self.ca, certfile=self.cert, keyfile=self.key, tls_version=ssl.PROTOCOL_TLSv1_2)

    def _on_connect(self, client, userdata, flags, rc):
        LOG.info("%s connected rc=%s", self.client_id, rc)

    def _on_disconnect(self, client, userdata, rc):
        LOG.warning("%s disconnected rc=%s", self.client_id, rc)

    def _on_publish(self, client, userdata, mid):
        LOG.debug("%s published mid=%s", self.client_id, mid)

    def set_message_callback(self, cb):
        self.client.on_message = cb

    def connect(self, keepalive=60):
        self.client.connect(self.endpoint, 8883, keepalive)
        self.client.loop_start()
        time.sleep(0.3)

    def disconnect(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            LOG.exception("disconnect failed")

    def publish(self, topic, payload, qos=1):
        return self.client.publish(topic, payload, qos=qos)

    def subscribe(self, topic, qos=1):
        return self.client.subscribe(topic, qos=qos)
