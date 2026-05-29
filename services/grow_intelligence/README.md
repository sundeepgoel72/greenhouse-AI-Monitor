# Grow Intelligence Service

## MVP Features

- Read image from Frigate snapshot
- Split image into four grow bag ROIs
- Calculate green coverage percentage
- Calculate yellow/brown coverage percentage
- Publish MQTT metrics
- Generate intervention alerts

## Planned Modules

main.py
vision.py
mqtt_client.py
rules.py
storage.py
frigate.py

## MQTT Topics

grow/bag1/metrics
grow/bag2/metrics
grow/bag3/metrics
grow/bag4/metrics

grow/bag1/alerts
grow/bag2/alerts
grow/bag3/alerts
grow/bag4/alerts

## Calibration

A screenshot from the rooftop_growhouse camera is required to finalise ROI coordinates.
