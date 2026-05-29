# Sensor Strategy

## MVP

Use 3 representative moisture sensors rather than 1 sensor per bed.

Reason:

- Lower cost
- Easier wiring
- Faster deployment
- Validate moisture variability before scaling

## Layout

Sensor A
- Front Left Bed

Sensor B
- Front Right Bed

Sensor C
- Middle Reference Bed

## Shared Sensors

SHT31
- Temperature
- Humidity

BH1750
- Lux

## Future Expansion

If moisture varies significantly between beds:

- Expand to 1 sensor per bed

Otherwise:

- Keep representative sensor model
