# AMRIT MQTT PUBLISHER
Small Python library to **publish CloudEvent messages over amrit notification center MQTT**.
It handles **validation**, **CloudEvent wrapping**, **MQTT connection (TLS/WebSocket)**, and **publishing**.

## Features
Functions :
- publish_alert_message : publish a single alert messages via MQTT
- publish_alert_messages : publish multiples alerts
- publish_alert_file : publish alert(s) contained in a JSON file.
- publish_simple_alert : to publish an alert by defining minimum expected mandatory attributes.

Automatic conversion from Python `dict` → validated Pydantic model. Alert_raw schema are provided.




## Installation 
Using [Poetry](https://python-poetry.org/):

```bash
poetry add amrit-mqtt-publisher
```
## Configuration
The following environment variables are needed : 

```text
MQTT_HOST_URL=mosquitto.isival.ifremer.fr
MQTT_USERNAME=XXXX
MQTT_PASSWORD=YYYYY
MQTT_DEFAULT_TOPIC=amrit/notification/raw/operations-alerts

```
## Usage:
See the **demo_scripts/send_test_alert.py** to have usage examples.

You can run the demo_scripts :
```bash
poetry run python demo_scripts/send_test_alert.py
```

Example of an alert to publish in form of a python dict : 

```text
mock_alert_1 = {
  "resource": '11111',
  "event": 'fake_alert',
  "environment": 'Development',
  "severity": 'informational',
  "correlate": [],  
  "service": ['euro-argo'],
  "group": 'argo float alarm',
  "value": "0",
  "text": 'test alert',  
  "attributes": {
    "Country": 'Spain',          
    "alert_category": 'Information',          
    "ArgoType": 'PSEUDO',
    "LastStationDate": '24-05-2025',
    "url":'https://fleetmonitoring.euro-argo.eu/float/5906990',        
    "lastCycleNumberToRaiseAlarm": '107',
  },
  "origin": 'test alert sender',
  "type": 'argo float alert demo',        
  "timeout": 120,
  "rawData": None             
}  
```

You can also use provided model (from amrit_mqtt_publisher.models import Alert_raw) to build the object to send by knowing which attributes are expected and which ones are mandatoru :

```text
mock_alert_1b= Alert_raw.Schema(
    resource='11111b',
    event='fake_alert',
    environment='Development',
    severity='informational',
    correlate=[],
    service=['euro-argo'],
    group='argo float alarm',
    value='0',
    text='test alert',
    attributes=Alert_raw.Attributes(
        Country='spain',
        alert_category='Information',
        LastStationDate='24-05-2025',
        url='https://fleetmonitoring.euro-argo.eu/float/5906990',
        lastCycleNumberToRaiseAlarm='107'
    ), # type: ignore
    origin='test alert sender',
    type='argo float alert demo',
    timeout=120,
    rawData=None
)

```

## Run with Docker
You can run your script in the docker container wich contain required environment.
- Build the image using Docker :

```bash
docker build -t amrit-mqtt-publisher
```

- Run your script inside the container :
```bash
docker run --rm --env-file .env -v ${pwd}/demo_scripts:/demo_scripts amrit-mqtt-publisher:latest /demo_scripts/send_test_alert.py
```
Mount other volume (for example input data) if necessary. In the demo script, you need to change files's path to absolute path to work in the container : 

 publish_alert_file("./demo_scripts/two_alerts.json","amrit/notification/raw/operations-alerts",stop_on_error=False )

=> 

publish_alert_file("/demo_scripts/two_alerts.json","amrit/notification/raw/operations-alerts",stop_on_error=False )

