from backend.services.mqtt_publisher import MqttPublisher


class MetricsEngine:
    def __init__(self):
        self.publisher = MqttPublisher()

    def process_results(self, analysis_results: list[dict]):
        for result in analysis_results:
            bed_id = result['bed_id']
            self.publisher.publish_bed_metrics(bed_id, result)
