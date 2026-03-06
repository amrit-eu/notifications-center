import os
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=False)

@dataclass(frozen=True)
class MqttConfig:
    mqtt_host: str
    mqtt_port: int 
    mqtt_tls:bool
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    use_websockets: bool = True
    client_id: str | None = None
    connect_timeout: float = 5.0
    default_topic: str | None = None

_DEFAULT = MqttConfig(
    mqtt_host=os.environ.get("MQTT_HOST_URL", ""),
    mqtt_port=int(os.environ.get("MQTT_HOST_PORT",443)),
    mqtt_tls= os.getenv("MQTT_USE_TLS", 'False').lower() in ('true', '1', 't'),
    mqtt_username=os.environ.get("MQTT_USERNAME"),
    mqtt_password=os.environ.get("MQTT_PASSWORD"),
    default_topic=os.environ.get("MQTT_DEFAULT_TOPIC"),
)

_current = _DEFAULT

def get_config() -> MqttConfig:
    return _current

def set_config(cfg: MqttConfig) -> None:
    global _current
    _current = cfg