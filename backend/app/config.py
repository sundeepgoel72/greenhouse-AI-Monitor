from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./greenhouse.db"
    frigate_base_url: str = "http://localhost:5000"
    frigate_camera: str = "Polyhouse"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    snapshot_dir: str = "./snapshots"

    class Config:
        env_file = ".env"

settings = Settings()
