import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Camera,
  CirclePlus,
  ClipboardList,
  Leaf,
  RefreshCw,
  Save,
  ThermometerSun,
  Trash2,
  Undo2,
  Upload,
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8088";

type Point = { x: number; y: number };
type Bed = {
  id: number;
  name: string;
  crop?: string | null;
  sowing_date?: string | null;
  transplant_date?: string | null;
  polygon: Point[];
};
type Snapshot = {
  id: number;
  timestamp: string;
  image_path: string;
  image_url: string;
};
type Metric = {
  id: number;
  bed_id: number;
  snapshot_id: number;
  green_pct: number;
  yellow_pct: number;
  soil_pct: number;
  created_at: string;
};
type MetricHistory = Metric & {
  snapshot_timestamp: string;
};
type Observation = {
  id: number;
  bed_id: number;
  kind: string;
  note?: string | null;
  created_at: string;
};
type Alert = {
  id: number;
  bed_id: number;
  severity: "info" | "warning" | "critical";
  message: string;
  created_at: string;
};
type SensorReading = {
  id: number;
  bed_id?: number | null;
  sensor_type: string;
  value: number;
  unit?: string | null;
  timestamp?: string | null;
  created_at: string;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers:
      init?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json() as Promise<T>;
}

function App() {
  const [beds, setBeds] = useState<Bed[]>([]);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [metricHistory, setMetricHistory] = useState<MetricHistory[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [sensorReadings, setSensorReadings] = useState<SensorReading[]>([]);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [selectedBedId, setSelectedBedId] = useState<number | null>(null);
  const [draftPolygon, setDraftPolygon] = useState<Point[]>([]);
  const [status, setStatus] = useState("Ready");
  const fileRef = useRef<HTMLInputElement>(null);

  const selectedBed = beds.find((bed) => bed.id === selectedBedId) ?? beds[0] ?? null;
  const latestByBed = useMemo(() => {
    const map = new Map<number, Metric>();
    for (const metric of metrics) {
      if (!map.has(metric.bed_id)) map.set(metric.bed_id, metric);
    }
    return map;
  }, [metrics]);

  async function load() {
    const [
      bedData,
      metricData,
      alertData,
      observationData,
      sensorReadingData,
      latestSnapshot,
    ] = await Promise.all([
      api<Bed[]>("/api/beds"),
      api<Metric[]>("/api/metrics?limit=80"),
      api<Alert[]>("/api/alerts?limit=20"),
      api<Observation[]>("/api/observations?limit=20"),
      api<SensorReading[]>("/api/sensor-readings?limit=40"),
      api<Snapshot | null>("/api/snapshots/latest"),
    ]);
    setBeds(bedData);
    setMetrics(metricData);
    setAlerts(alertData);
    setObservations(observationData);
    setSensorReadings(sensorReadingData);
    setSnapshot(latestSnapshot);
    if (!selectedBedId && bedData.length > 0) {
      setSelectedBedId(bedData[0].id);
      setDraftPolygon(bedData[0].polygon);
    }
  }

  useEffect(() => {
    load().catch((error) => setStatus(error.message));
  }, []);

  useEffect(() => {
    if (selectedBed) setDraftPolygon(selectedBed.polygon);
  }, [selectedBedId, beds.length]);

  useEffect(() => {
    if (!selectedBed?.id) {
      setMetricHistory([]);
      return;
    }
    api<MetricHistory[]>(`/api/beds/${selectedBed.id}/metrics/history?limit=24`)
      .then(setMetricHistory)
      .catch((error) => setStatus(error.message));
  }, [selectedBed?.id, metrics.length]);

  async function seedBeds() {
    const defaults = [
      { name: "Bed 1", crop: "Unassigned" },
      { name: "Bed 2", crop: "Unassigned" },
      { name: "Bed 3", crop: "Unassigned" },
      { name: "Bed 4", crop: "Unassigned" },
    ];
    setStatus("Creating beds");
    for (const bed of defaults) {
      await api<Bed>("/api/beds", {
        method: "POST",
        body: JSON.stringify({ ...bed, polygon: [] }),
      });
    }
    await load();
    setStatus("Beds ready");
  }

  async function ingestFrigate() {
    setStatus("Fetching Frigate snapshot");
    const result = await api<{ snapshot: Snapshot; metrics: Metric[]; alerts: Alert[] }>(
      "/api/ingest/frigate",
      {
        method: "POST",
      },
    );
    setSnapshot(result.snapshot);
    await load();
    setStatus("Snapshot processed");
  }

  async function uploadSnapshot(file: File) {
    const form = new FormData();
    form.append("image", file);
    setStatus("Uploading snapshot");
    const result = await api<{ snapshot: Snapshot; metrics: Metric[]; alerts: Alert[] }>(
      "/api/ingest/upload",
      {
        method: "POST",
        body: form,
      },
    );
    setSnapshot(result.snapshot);
    await load();
    setStatus("Snapshot processed");
  }

  async function savePolygon() {
    if (!selectedBed) return;
    setStatus("Saving ROI");
    await api<Bed>(`/api/beds/${selectedBed.id}`, {
      method: "PUT",
      body: JSON.stringify({ polygon: draftPolygon }),
    });
    await load();
    setStatus("ROI saved");
  }

  async function ingestHomeAssistant() {
    setStatus("Syncing Home Assistant");
    await api<SensorReading[]>("/api/sensor-readings/home-assistant", {
      method: "POST",
    });
    await load();
    setStatus("Sensors synced");
  }

  async function addObservation(formData: FormData) {
    const bedId = Number(formData.get("bed_id"));
    const kind = String(formData.get("kind"));
    const note = String(formData.get("note") || "");
    await api<Observation>("/api/observations", {
      method: "POST",
      body: JSON.stringify({ bed_id: bedId, kind, note }),
    });
    await load();
  }

  return (
    <main>
      <header className="app-header">
        <div>
          <h1>Greenhouse AI Monitor</h1>
          <p>{status}</p>
        </div>
        <div className="actions">
          <button title="Refresh" onClick={() => load()}>
            <RefreshCw size={18} />
            Refresh
          </button>
          <button title="Fetch Frigate snapshot" onClick={() => ingestFrigate()}>
            <Camera size={18} />
            Frigate
          </button>
          <button
            title="Sync Home Assistant sensors"
            onClick={() => ingestHomeAssistant().catch((error) => setStatus(error.message))}
          >
            <ThermometerSun size={18} />
            Sensors
          </button>
          <button title="Upload snapshot" onClick={() => fileRef.current?.click()}>
            <Upload size={18} />
            Upload
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) uploadSnapshot(file).catch((error) => setStatus(error.message));
            }}
          />
        </div>
      </header>

      {beds.length === 0 ? (
        <section className="empty-state">
          <Leaf size={32} />
          <h2>Four monitored beds</h2>
          <button onClick={() => seedBeds()}>
            <CirclePlus size={18} />
            Create
          </button>
        </section>
      ) : (
        <>
          <section className="metrics-grid">
            {beds.map((bed) => (
              <BedMetricCard
                key={bed.id}
                bed={bed}
                metric={latestByBed.get(bed.id)}
                active={selectedBed?.id === bed.id}
                onClick={() => setSelectedBedId(bed.id)}
              />
            ))}
          </section>

          <section className="workspace">
            <RoiCalibrator
              beds={beds}
              selectedBed={selectedBed}
              snapshot={snapshot}
              draftPolygon={draftPolygon}
              setDraftPolygon={setDraftPolygon}
              setSelectedBedId={setSelectedBedId}
              savePolygon={() => savePolygon().catch((error) => setStatus(error.message))}
            />
            <aside className="side-panel">
              <AlertList alerts={alerts} beds={beds} />
              <SensorPanel readings={sensorReadings} beds={beds} />
              <TrendPanel bed={selectedBed} history={metricHistory} />
              <MetricsTable beds={beds} metrics={metrics.slice(0, 12)} />
              <ObservationForm beds={beds} onSubmit={addObservation} />
              <ObservationList observations={observations} beds={beds} />
            </aside>
          </section>
        </>
      )}
    </main>
  );
}

function BedMetricCard({
  bed,
  metric,
  active,
  onClick,
}: {
  bed: Bed;
  metric?: Metric;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button className={`metric-card ${active ? "active" : ""}`} onClick={onClick}>
      <span className="bed-name">{bed.name}</span>
      <span className="crop">{bed.crop || "Unassigned"}</span>
      <div className="metric-row">
        <MetricValue label="Green" value={metric?.green_pct} />
        <MetricValue label="Yellow" value={metric?.yellow_pct} />
        <MetricValue label="Soil" value={metric?.soil_pct} />
      </div>
    </button>
  );
}

function MetricValue({ label, value }: { label: string; value?: number }) {
  return (
    <span>
      <strong>{value === undefined ? "--" : value.toFixed(1)}</strong>
      <small>{label}</small>
    </span>
  );
}

function RoiCalibrator({
  beds,
  selectedBed,
  snapshot,
  draftPolygon,
  setDraftPolygon,
  setSelectedBedId,
  savePolygon,
}: {
  beds: Bed[];
  selectedBed: Bed | null;
  snapshot: Snapshot | null;
  draftPolygon: Point[];
  setDraftPolygon: (polygon: Point[]) => void;
  setSelectedBedId: (id: number) => void;
  savePolygon: () => void;
}) {
  const imageRef = useRef<HTMLImageElement>(null);
  const [imageSize, setImageSize] = useState({ width: 1, height: 1 });
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const imageUrl = snapshot ? `${API_BASE}${snapshot.image_url}` : "";

  function pointFromEvent(event: React.PointerEvent<HTMLDivElement>): Point | null {
    const image = imageRef.current;
    if (!image) return null;
    const rect = image.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * image.naturalWidth;
    const y = ((event.clientY - rect.top) / rect.height) * image.naturalHeight;
    return {
      x: Math.min(Math.max(0, x), image.naturalWidth),
      y: Math.min(Math.max(0, y), image.naturalHeight),
    };
  }

  function addPoint(event: React.PointerEvent<HTMLDivElement>) {
    if ((event.target as Element).closest("[data-roi-handle]")) return;
    const point = pointFromEvent(event);
    if (!point) return;
    setDraftPolygon([...draftPolygon, point]);
  }

  function movePoint(event: React.PointerEvent<HTMLDivElement>) {
    if (dragIndex === null) return;
    const point = pointFromEvent(event);
    if (!point) return;
    setDraftPolygon(
      draftPolygon.map((current, index) => (index === dragIndex ? point : current)),
    );
  }

  return (
    <section className="calibrator">
      <div className="section-title">
        <h2>ROI Calibration</h2>
        <div className="toolbar">
          <select
            value={selectedBed?.id ?? ""}
            onChange={(event) => setSelectedBedId(Number(event.target.value))}
          >
            {beds.map((bed) => (
              <option key={bed.id} value={bed.id}>
                {bed.name}
              </option>
            ))}
          </select>
          <button title="Clear polygon" onClick={() => setDraftPolygon([])}>
            <Trash2 size={18} />
          </button>
          <button
            title="Undo last point"
            onClick={() => setDraftPolygon(draftPolygon.slice(0, -1))}
          >
            <Undo2 size={18} />
          </button>
          <button title="Save ROI" onClick={savePolygon}>
            <Save size={18} />
            Save
          </button>
        </div>
      </div>
      <div
        className="canvas"
        onPointerDown={addPoint}
        onPointerMove={movePoint}
        onPointerUp={() => setDragIndex(null)}
        onPointerLeave={() => setDragIndex(null)}
      >
        {snapshot ? (
          <>
            <img
              ref={imageRef}
              src={imageUrl}
              alt="Latest greenhouse snapshot"
              onLoad={(event) =>
                setImageSize({
                  width: event.currentTarget.naturalWidth || 1,
                  height: event.currentTarget.naturalHeight || 1,
                })
              }
            />
            <svg className="overlay" viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}>
              {draftPolygon.length > 1 && (
                <polygon
                  points={draftPolygon.map((point) => `${point.x},${point.y}`).join(" ")}
                  className="roi-shape"
                />
              )}
              {draftPolygon.map((point, index) => (
                <circle
                  key={`${point.x}-${point.y}-${index}`}
                  cx={point.x}
                  cy={point.y}
                  r="9"
                  data-roi-handle
                  onPointerDown={(event) => {
                    event.stopPropagation();
                    setDragIndex(index);
                  }}
                />
              ))}
            </svg>
          </>
        ) : (
          <div className="snapshot-placeholder">
            <Camera size={30} />
            <span>No snapshot</span>
          </div>
        )}
      </div>
    </section>
  );
}

function TrendPanel({ bed, history }: { bed: Bed | null; history: MetricHistory[] }) {
  return (
    <section className="panel">
      <h2>Trend{bed ? ` · ${bed.name}` : ""}</h2>
      {history.length < 2 ? (
        <span className="muted">Need at least two snapshots</span>
      ) : (
        <div className="trend-stack">
          <Sparkline label="Green" color="#2e7d4f" values={history.map((item) => item.green_pct)} />
          <Sparkline
            label="Yellow"
            color="#c58c18"
            values={history.map((item) => item.yellow_pct)}
          />
          <Sparkline label="Soil" color="#7b5b3a" values={history.map((item) => item.soil_pct)} />
        </div>
      )}
    </section>
  );
}

function Sparkline({
  label,
  color,
  values,
}: {
  label: string;
  color: string;
  values: number[];
}) {
  const width = 220;
  const height = 46;
  const points = values
    .map((value, index) => {
      const x = values.length === 1 ? 0 : (index / (values.length - 1)) * width;
      const y = height - (Math.min(Math.max(value, 0), 100) / 100) * height;
      return `${x},${y}`;
    })
    .join(" ");
  const latest = values[values.length - 1] ?? 0;

  return (
    <div className="sparkline-row">
      <div>
        <strong>{latest.toFixed(1)}%</strong>
        <span>{label}</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <polyline points={points} fill="none" stroke={color} strokeWidth="3" />
      </svg>
    </div>
  );
}

function AlertList({ alerts, beds }: { alerts: Alert[]; beds: Bed[] }) {
  const bedName = (id: number) => beds.find((bed) => bed.id === id)?.name ?? `Bed ${id}`;
  return (
    <section className="panel">
      <h2>Alerts</h2>
      <div className="alert-list">
        {alerts.length === 0 ? (
          <span className="muted">No recent alerts</span>
        ) : (
          alerts.map((alert) => (
            <div key={alert.id} className={`alert ${alert.severity}`}>
              <strong>
                {alert.severity} · {bedName(alert.bed_id)}
              </strong>
              <span>{alert.message}</span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function SensorPanel({ readings, beds }: { readings: SensorReading[]; beds: Bed[] }) {
  const bedName = (id?: number | null) =>
    id ? beds.find((bed) => bed.id === id)?.name ?? `Bed ${id}` : "Polyhouse";
  const latest = new Map<string, SensorReading>();
  for (const reading of readings) {
    const key = `${reading.bed_id ?? "site"}:${reading.sensor_type}`;
    if (!latest.has(key)) latest.set(key, reading);
  }

  return (
    <section className="panel">
      <h2>Sensors</h2>
      <div className="sensor-grid">
        {[...latest.values()].length === 0 ? (
          <span className="muted">No sensor readings</span>
        ) : (
          [...latest.values()].map((reading) => (
            <div key={reading.id} className="sensor-reading">
              <span>{bedName(reading.bed_id)}</span>
              <strong>
                {reading.value.toFixed(1)}
                {reading.unit || ""}
              </strong>
              <small>{reading.sensor_type}</small>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function MetricsTable({ beds, metrics }: { beds: Bed[]; metrics: Metric[] }) {
  const bedName = (id: number) => beds.find((bed) => bed.id === id)?.name ?? `Bed ${id}`;
  return (
    <section className="panel">
      <h2>Metrics</h2>
      <table>
        <thead>
          <tr>
            <th>Bed</th>
            <th>Green</th>
            <th>Yellow</th>
            <th>Soil</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => (
            <tr key={metric.id}>
              <td>{bedName(metric.bed_id)}</td>
              <td>{metric.green_pct.toFixed(1)}%</td>
              <td>{metric.yellow_pct.toFixed(1)}%</td>
              <td>{metric.soil_pct.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function ObservationForm({
  beds,
  onSubmit,
}: {
  beds: Bed[];
  onSubmit: (formData: FormData) => Promise<void>;
}) {
  const formRef = useRef<HTMLFormElement>(null);
  return (
    <section className="panel">
      <h2>Observation</h2>
      <form
        ref={formRef}
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit(new FormData(event.currentTarget)).then(() => formRef.current?.reset());
        }}
      >
        <select name="bed_id">
          {beds.map((bed) => (
            <option key={bed.id} value={bed.id}>
              {bed.name}
            </option>
          ))}
        </select>
        <select name="kind">
          {["Watered", "Fertilized", "Pruned", "Harvested", "Note"].map((kind) => (
            <option key={kind} value={kind}>
              {kind}
            </option>
          ))}
        </select>
        <input name="note" placeholder="Note" />
        <button>
          <ClipboardList size={18} />
          Add
        </button>
      </form>
    </section>
  );
}

function ObservationList({
  observations,
  beds,
}: {
  observations: Observation[];
  beds: Bed[];
}) {
  const bedName = (id: number) => beds.find((bed) => bed.id === id)?.name ?? `Bed ${id}`;
  return (
    <section className="panel">
      <h2>Recent</h2>
      <div className="observation-list">
        {observations.map((observation) => (
          <div key={observation.id} className="observation">
            <strong>
              {observation.kind} · {bedName(observation.bed_id)}
            </strong>
            <span>{observation.note || new Date(observation.created_at).toLocaleString()}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
