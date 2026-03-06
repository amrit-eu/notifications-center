

import json
from typing import Any, Iterable, List, Set

from amrit_mqtt_publisher._mqtt.mqtt_client import _MqttPublisher
from amrit_mqtt_publisher.config import MqttConfig, get_config, set_config
from amrit_mqtt_publisher.models import Alert_raw, CloudEventAlertaRaw
from amrit_mqtt_publisher.utils.builders import cloud_event_builder

_client: _MqttPublisher | None = None

# get the mqtt client singleton :
def _client_singleton() -> _MqttPublisher:
    global _client
    if _client is None:
        _client = _MqttPublisher()
    return _client


def _publish_one(alert: dict [str, Any] | Alert_raw.Schema, topic: str | None = None, retain: bool = False ):
    """Mqtt publication wrapper.
    It validate the alert format
    Serialize in JSON
    Publish on MQTT
    """
    alert_model = alert if isinstance(alert,Alert_raw.Schema ) else Alert_raw.Schema(**alert)
    # build cloud event
    cloud_event_model = cloud_event_builder (alert_model)
    #convert to json str:
    body = cloud_event_model.model_dump_json()

    # topic :
    t = topic or get_config().default_topic
    if not t:
        raise ValueError("Topic must be defined in argument or environment variable MQTT_DEFAULT_TOPIC")
    # send message :
    _client_singleton().publish(body, t, retain)

# -- public API : SINGLE ----------------------------------------------------
def publish_alert_message (alert: dict [str, Any] | Alert_raw.Schema, topic: str | None = None, retain: bool = False):
    """Publish a single CloudEvent alert message to the MQTT broker.

    Validates the input (dict or `Alert_raw.Schema`), build the CloudEvent message, serializes it to JSON,
    and sends it to the given MQTT topic.

    Parameters
    ----------
    alert : Alert_raw.Schema | dict[str, Any]
        The alert payload to publish.
    topic : str | None, optional
        MQTT topic. Defaults to the configured `default_topic`.
    retain : bool, optional
        Whether to retain messages on the broker (default: False).

    Raises
    ------
    ValueError
        If no topic is provided or configured.
    ValidationError
        If payload validation fails.

    """
    _publish_one(alert, topic, retain)

    _client_singleton().disconnect()

def publish_simple_alert (resource:str, event:str, service: list[str],alert_category:Alert_raw.AlertCategory, severity: Alert_raw.Severity = Alert_raw.Severity.normal, country: str= "Unknown",  topic: str | None = None, retain: bool = False) :
    """
    To publish an alert by defining minimum expected mandatory attributes.

    Parameters
    ----------
    resource: str
        Unique identifier of resource under alarm.
    event: str
        event name
    severity: Severity
        Severity of alert (default normal)
    topic : str | None, optional
        MQTT topic. Defaults to the configured `default_topic`.
    retain : bool, optional
        Whether to retain messages on the broker (default: False).

    """
    #build the Attributes object
    attributes =  Alert_raw.Attributes (Country=country, alert_category=alert_category) # type: ignore
    # build the alert_Raw object
    alert = Alert_raw.Schema(
        resource=resource,
        event=event,
        severity=severity,
        environment='Development',
        service=service, 
        attributes=attributes
    ) # type: ignore
    # publish alert
    publish_alert_message(alert, topic, retain)


# -- public API : MUTLIPLES MESSAGES ----------------------------------------------------
def publish_alert_messages(alert_cloud_events_list: Iterable[dict [str, Any] | Alert_raw.Schema], topic: str | None = None, retain: bool = False, stop_on_error: bool = True):
    """Publish multiple CloudEvent alert messages to the MQTT broker.

    Each message is validated and published individually.

    Parameters
    ----------
    alerts : Iterable[Alert_raw.Schema | dict[str, Any]]
        Sequence of alert payloads to publish.
    topic : str | None, optional
        MQTT topic. Defaults to the configured `default_topic`.
    retain : bool, optional
        Whether to retain messages on the broker (default: False).
    stop_on_error : bool, optional
        If True (default), stops at the first error.
        If False, continues and returns an error summary.

    Returns
    -------
    dict[str, Any]
        Summary with keys:
          - "sent": number of successful publishes
          - "errors": list of errors (if any)

    """
    # to save result by alerts
    sent =0
    errors : list[dict[str, Any]]=[]

    for index, alert_cloud_event in enumerate(alert_cloud_events_list) :
        try :
            _publish_one(alert_cloud_event, topic=topic, retain=retain)
            sent += 1
        except Exception as e:
            if (stop_on_error):
                _client_singleton().disconnect()
                raise
            errors.append({"index": index, "error": repr(e) })
    
    _client_singleton().disconnect()

    return {"sent": sent, "errors": errors}

  

def publish_alert_file(path: str, topic: str | None = None, retain: bool = False, stop_on_error: bool = True):
    """Publish the json content of a file on the mqtt.
    The json must be compliant with the alert Cloud Event format.

    """
    with open(path, "rb") as f:
        data = json.load(f)
    if isinstance(data, list) :
        return publish_alert_messages(data, topic=topic, retain=retain, stop_on_error=stop_on_error)
       
    elif isinstance(data, dict) :
        publish_alert_message(data, topic=topic, retain=retain)
        return {"sent": 1, "errors": []}

    raise ValueError("JSON file root must be an object or an array of objects.")
    

def configure (**kwargs) -> None :
    cfg=get_config()
    # Create a new MqttConfig by merging the existing one with the arguments provided by user :
    new_mqtt_config = MqttConfig(**{**cfg.__dict__, **kwargs})
    # save the new config as global config 
    set_config(new_mqtt_config)
    # reset mqtt client that It would init again with new config :
    global _client
    _client = None