from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./greenhouse.db"
    frigate_base_url: str = "http://localhost:5000"
    frigate_camera: str = "rooftop_growhouse"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    snapshot_dir: str = "./snapshots"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    green_hsv_lower: str = "35,35,35"
    green_hsv_upper: str = "90,255,255"
    yellow_hsv_lower: str = "18,45,45"
    yellow_hsv_upper: str = "34,255,255"
    soil_hsv_lower: str = "5,20,20"
    soil_hsv_upper: str = "25,210,220"
    alert_green_critical_below: float = 15
    alert_green_warning_below: float = 30
    alert_yellow_critical_above: float = 15
    alert_yellow_warning_above: float = 8
    alert_soil_warning_above: float = 65

    class Config:
        env_file = ".env"


settings = Settings()
