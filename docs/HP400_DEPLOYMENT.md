# HP400 Deployment

## Directory

```bash
cd /opt
sudo git clone <repo>
cd greenhouse-AI-Monitor
```

## Configure

Create .env

```env
FRIGATE_BASE_URL=http://FRIGATE_IP:5000
FRIGATE_CAMERA=RoofBigPolyhouse

MQTT_HOST=192.168.1.10
MQTT_PORT=1883

DAY_START=06:30
DAY_END=18:30

NORMAL_INTERVAL_SECONDS=900
PEAK_INTERVAL_SECONDS=300
```

## Run

```bash
docker compose up -d --build
```

## Storage

Snapshots:

storage/snapshots/

Metrics:

storage/metrics/
```
