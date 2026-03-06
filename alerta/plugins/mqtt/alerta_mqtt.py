from datetime import datetime, timezone
import sys
from alerta.models.alert import Alert
import os
import logging
from uuid import uuid4
import paho.mqtt.client as mqtt
import time



from alerta.plugins import PluginBase
from models import Alert_processed, CloudEventAlertaProcessed

try:
    from alerta.plugins import app  # alerta >= 5.0
except ImportError:
    from alerta.app import app  # alerta < 5.0

# LOGGING CONFIGURATION ----------
LOG = logging.getLogger('alerta.plugins.mqtt')
LOG.setLevel(logging.INFO)

#Créez un gestionnaire de flux (console) avec un format personnalisé
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
handler.setFormatter(formatter)

# Ajoutez le gestionnaire au logger
LOG.addHandler(handler)

# ----------------------------------

# DEFAULT VALUE :
DEFAULT_MQTT_HOST_URL = 'mosquitto.isival.ifremer.fr'
DEFAULT_MQTT_HOST_PORT = 443
DEFAULT_MQTT_TOPIC_PUB= 'amrit/notification/processed'

MQTT_HOST_URL = os.environ.get('MQTT_HOST_URL') or os.getenv('MQTT_HOST_URL') or app.config.get('MQTT_HOST_URL', DEFAULT_MQTT_HOST_URL)
MQTT_HOST_PORT = os.environ.get('MQTT_HOST_PORT') or os.getenv('MQTT_HOST_PORT') or app.config.get('MQTT_HOST_PORT', DEFAULT_MQTT_HOST_PORT)
MQTT_TOPIC_PUB= os.environ.get('MQTT_TOPIC_ALERTA_PROCESSED_PUB') or os.getenv('MQTT_TOPIC_ALERTA_PROCESSED_PUB') or app.config.get('MQTT_TOPIC_ALERTA_PROCESSED_PUB', DEFAULT_MQTT_TOPIC_PUB)
MQTT_USERNAME_RW = os.environ.get('MQTT_USERNAME_RW') or os.getenv('MQTT_USERNAME_RW') or app.config.get('MQTT_USERNAME_RW') or None
MQTT_PASSWORD_RW = os.environ.get('MQTT_PASSWORD_RW') or os.getenv('MQTT_PASSWORD_RW') or app.config.get('MQTT_PASSWORD_RW') or None
MQTT_USE_TLS= os.getenv('MQTT_USE_TLS', 'false').lower() in ('true', '1', 'yes')

class MqttPublisher (PluginBase):

    def __init__(self, name=None): 
        # Create MQTT client with websockets :
        self.client = mqtt.Client(transport="websockets")
        if (MQTT_USE_TLS) :
            self.client.tls_set()        

        # Add auth ids :
        if MQTT_USERNAME_RW is not None and MQTT_PASSWORD_RW is not None :
            LOG.info("setting up client username and password")
            self.client.username_pw_set(MQTT_USERNAME_RW, MQTT_PASSWORD_RW)
        

        # set up callbacks :
        self.client.on_connect = self.on_connect

        # connection is made in post_receive when an alert is receive.  :
        self.clientConnected = False

        LOG.info("plugin MQTT started")

        super().__init__(name)
  
    def pre_receive(self, alert):
       
        # reject or modify an alert before it hits the database

        return alert

    def post_receive(self, alert ):
        LOG.info(f"An Alert has been processed : {alert.resource} - {alert.event}")
        # Because Alerta run on multiple workers which are started and destroyed continuesly. So the plugin cannot maintain an unique connection to mqtt. It is closed each time a worker is destroyed. Need to verify the connection and connect to MQTT when an alert is received :
        if (not self.clientConnected) :
            LOG.info ("MQTT client not connected to broker, try to connect...")
             # Connect to broker :
            try :
                self.client.connect(MQTT_HOST_URL,int(MQTT_HOST_PORT),60)
                self.client.loop_start()
            except Exception as connexion_error :
                LOG.exception(f"MQTT connection error: {connexion_error}")
                return
            # wait to be connected to MQTT before trying to publish
            timeout = time.time() + 5  # max 5s
            while not self.clientConnected:
                if time.time() > timeout:
                    LOG.error("Timeout waiting for MQTT connection")
                    return
                time.sleep(0.1)
        

        # retrieve payload of alert and build a cloudEvent payload :
        try :
            alertProcessed = alertProcessedBuilder (alert)
            cloudevent_payload = cloudEventBuilder(alertProcessed)
            # convert to json body :
            json_payload = cloudevent_payload.model_dump_json(indent=2)
        except Exception as build_err:
            LOG.exception(f"Error building CloudEvent payload: {build_err}")
            return
        
        # adatap the PUB topic with the "topic" attribute if present in alert object.
        # If alert come from the mqtt, the attribut will be present. If not (example : POST from API), add the default one 'operations-alerts'
        # TO DO : add a lookup table to determine topic from alert_category which is a mandatory attribute
        if (cloudevent_payload.data.attributes.mqtt_topic) :
            specificTopic = cloudevent_payload.data.attributes.mqtt_topic.value
        else :
            specificTopic = "operations-alerts"

        mqttTopicToPublishTo = MQTT_TOPIC_PUB +"/"+specificTopic

        LOG.info(f"Publishing CloudEvent '{cloudevent_payload.type}' to MQTT topic : {mqttTopicToPublishTo}")
        try :
            publishResult = self.client.publish(mqttTopicToPublishTo, json_payload)
            if publishResult.rc != 0:
                LOG.error(f"Failed to publish message to MQTT. Return code: {publishResult.rc}")
        except Exception as e:
            LOG.exception(f"Unexpected error in post_receive: {e}")


        return

    def status_change(self, alert, status, text):
        # triggered by external status changes, used by integrations
        return
    
    # Callback when connection with MQTT broker is done
    def on_connect (self, client, userdata, flags, rc):   
        if rc == 0:
            LOG.info("Successful connection to MQTT broker")
            self.clientConnected=True
            # client.subscribe(TOPIC_SUB)  # Susbcribe to a topic
        else:
            LOG.error(f"Connection has failed, error code : {rc}")

def cloudEventBuilder(alertProcessed : Alert_processed.Schema):
    return CloudEventAlertaProcessed(
        id = str(uuid4()),
        specversion= "1.0",
        type=alertProcessed.event,
        source=alertProcessed.origin,
        datacontenttype="application/json",
        subject=alertProcessed.resource,
        time=datetime.now(timezone.utc).isoformat(),
        data=alertProcessed
    )    
    
def alertProcessedBuilder(alert : Alert) :
    return Alert_processed.Schema(
        id=alert.id,
        customer=alert.customer,
        duplicateCount=alert.duplicate_count,
        repeat=alert.repeat,
        previousSeverity=alert.previous_severity,
        trendIndication=alert.trend_indication,
        receiveTime=alert.receive_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        lastReceiveId=alert.last_receive_id,
        updateTime=alert.update_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        history=[h.serialize for h in alert.history],

        resource=alert.resource,
        event=alert.event,
        environment=alert.environment,
        severity=alert.severity,
        correlate=alert.correlate,
        status=alert.status,
        service=alert.service,
        group=alert.group,
        value=alert.value,
        text=alert.text,
        tags=alert.tags,
        attributes=alert.attributes,
        origin=alert.origin,
        type=alert.event_type,
        createTime=alert.create_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        timeout=alert.timeout,
        rawData=alert.raw_data
    )
