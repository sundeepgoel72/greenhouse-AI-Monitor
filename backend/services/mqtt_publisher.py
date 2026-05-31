import json
import logging

import paho.mqtt.client as mqtt

from app.config import settings

logger = logging.getLogger(__name__)


class MqttPublisher:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.host = settings.mqtt_host
        self.port = settings.mqtt_port
        self.connected = False
        if settings.mqtt_username:
            self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        try:
            self.client.connect(self.host, self.port, 60)
            self.connected = True
        except OSError as exc:
            logger.warning("MQTT broker unavailable at %s:%s: %s", self.host, self.port, exc)

    @staticmethod
    def bed_topic(kind: str, bed_id: int | str) -> str:
        return f"grow/bed{bed_id}/{kind}"

    def publish_bed_metrics(self, bed_id: int | str, metrics: dict) -> None:
        self.publish(self.bed_topic("metrics", bed_id), metrics, retain=True)

    def publish_bed_alert(self, bed_id: int | str, alert: dict) -> None:
        self.publish(self.bed_topic("alerts", bed_id), alert, retain=False)

    def publish(self, topic: str, payload: dict, retain: bool = False) -> None:
        if not self.connected:
            return
        try:
            self.client.publish(topic, json.dumps(payload, default=str), retain=retain)
        except OSError as exc:
            logger.warning("MQTT publish failed for %s: %s", topic, exc)
