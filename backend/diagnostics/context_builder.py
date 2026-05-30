from datetime import date


def build_context(bed: dict, metrics: dict | None = None, sensors: dict | None = None) -> dict:
    metrics = metrics or {}
    sensors = sensors or {}

    age_days = None
    sowing_date = bed.get('sowing_date')

    if sowing_date:
        try:
            age_days = (date.today() - date.fromisoformat(sowing_date)).days
        except Exception:
            pass

    return {
        'bed_id': bed.get('id'),
        'crop': bed.get('crop'),
        'age_days': age_days,
        'green_pct': metrics.get('green_pct'),
        'yellow_pct': metrics.get('yellow_pct'),
        'soil_pct': metrics.get('soil_pct'),
        'temperature_c': sensors.get('temperature_c'),
        'humidity_pct': sensors.get('humidity_pct'),
        'lux': sensors.get('lux'),
        'moisture_pct': sensors.get('moisture_pct'),
    }
