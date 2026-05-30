import os
from .provider import DiagnosisProvider


class GeminiProvider(DiagnosisProvider):

    async def diagnose(self, image_path: str, context: dict) -> dict:
        api_key = os.getenv('GEMINI_API_KEY')

        if not api_key:
            return {
                'status': 'error',
                'diagnosis': None,
                'confidence': 0,
                'recommendations': ['GEMINI_API_KEY not configured']
            }

        return {
            'status': 'pending_implementation',
            'diagnosis': None,
            'confidence': 0,
            'recommendations': []
        }
