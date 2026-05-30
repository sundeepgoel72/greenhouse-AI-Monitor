from .provider import DiagnosisProvider


class NotConfiguredProvider(DiagnosisProvider):
    async def diagnose(self, image_path: str, context: dict) -> dict:
        return {
            'status': 'not_configured',
            'diagnosis': None,
            'confidence': 0,
            'recommendations': []
        }


def get_provider(provider_name: str) -> DiagnosisProvider:
    return NotConfiguredProvider()
