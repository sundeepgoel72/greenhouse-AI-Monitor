import json
import os
import paho.mqtt.client as mqtt


class MqttPublisher:
    def __init__(self):
        self.client = mqtt.Client()
        self.host = os.getenv('MQTT_HOST', 'localhost')
        self.port = int(os.getenv('MQTT_PORT', '1883'))
        self.client.connect(self.host, self.port, 60)

    def publish_bed_metrics(self, bed_id: str, metrics: dict):
        topic = f'grow/{bed_id}/metrics'
        self.client.publish(topic, json.dumps(metrics), retain=True)
