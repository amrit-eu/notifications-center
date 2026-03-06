import sys
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import logging
import os
from pydantic import ValidationError

from alertaclient.api import Client
import time

from models.Alert_raw import MqttTopic
from models import CloudEventAlertaRaw

DEFAULT_MQTT_HOST_URL = 'mosquitto.isival.ifremer.fr'
DEFAULT_MQTT_HOST_PORT = 443
DEFAULT_MQTT_TOPIC_SUB= 'amrit/notification/raw/#'

MQTT_HOST_URL = os.environ.get('MQTT_HOST_URL') or os.getenv('MQTT_HOST_URL') or  DEFAULT_MQTT_HOST_URL
MQTT_HOST_PORT = os.environ.get('MQTT_HOST_PORT') or os.getenv('MQTT_HOST_PORT') or DEFAULT_MQTT_HOST_PORT
MQTT_USE_TLS= os.getenv('MQTT_USE_TLS', 'false').lower() in ('true', '1', 'yes')
MQTT_TOPIC_SUB= os.environ.get('MQTT_TOPIC_ALERTA_RAW_SUB') or os.getenv('MQTT_TOPIC_ALERTA_RAW_SUB') or DEFAULT_MQTT_TOPIC_SUB
MQTT_USERNAME_RO = os.environ.get('MQTT_USERNAME_RO') or os.getenv('MQTT_USERNAME_RO')  or None
MQTT_PASSWORD_RO = os.environ.get('MQTT_PASSWORD_RO') or os.getenv('MQTT_PASSWORD_RO') or None

ALERTA_API_KEY = os.environ.get('ADMIN_KEY') or os.getenv('ADMIN_KEY')
#because run on same container than alert, use the default value :
ALERTA_ENDPOINT ="http://localhost:8080/api"

# init logging : 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)

LOG = logging.getLogger('mqttToAlerta.service')



# calback when connected to MQTT borker
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        LOG.info("MqttToAerta service successfuly connected to MQTT broker")
        time.sleep(0.1)
        # subscribe to general amrit notification "raw" topic
        client.subscribe(MQTT_TOPIC_SUB)
        LOG.info(f"MqttToAerta service successfulysSubscribed to topic: {MQTT_TOPIC_SUB}")
    else:
        LOG.error(f"MqttToAerta service failed to connect to MQTT broker. error code  : {rc}")

# calback when a message is received: 
def on_message (client, userdata, msg):
    try: 
        LOG.info("Message received on topic : " + msg.topic)
        # TO DO : get the topic name from msg.topic and add it to the alert's attributes attribute "topic"
        processMessage(msg, userdata)
    except Exception as e:
        LOG.exception (f"Unhandled exception : {e}")



def processMessage(msg, userdata) :
    try  :
        # extract cloudEvent object from message (will raise an error if not well formated !)
        payload = msg.payload.decode("utf-8")
        cloudEvent = CloudEventAlertaRaw.model_validate_json(payload)
        LOG.info ("cloud event received :" + cloudEvent.data.resource  +" - "+cloudEvent.data.event)
        alerta_obj = cloudEvent.data
        # add topic attribute :       
        try:
            alerta_obj.attributes.mqtt_topic = MqttTopic(getAlertSpecificTopicFromMqttMsg(msg))
        except ValueError:
            LOG.error(f"MQTT topic '{msg.topic}' not in known. Only authorized are {MqttTopic._member_names_}")

        sendAlertToAlerta(alerta_obj, userdata)
    except ValueError as e:
        LOG.error(f"ValueError while decoding message: {e}")
    except Exception as e:
        LOG.exception(f"Failed to process MQTT message: {e}")
    

    
def sendAlertToAlerta (alertObj, userdata):
    alertaClient = userdata["alertaClient"]
    try :   
        LOG.info ("Forwarding alert data to Alerta...")        
        alert_dict = alertObj.model_dump(mode="json")
        alertaClient.send_alert(**alert_dict)
        LOG.info ("alert data forwarded to Alerta.")
    except Exception as e:
        LOG.exception(f"Failed to send alert to Alerta: {e}")
    


def getAlertSpecificTopicFromMqttMsg (msg):
    """
    From mqtt topics like topic = "amrit/notification/raw/support-requests" get the most specific one (eg s"upport-requests")
    """
    rawMqttTopic = msg.topic
    lastSpecificTopic = rawMqttTopic.rsplit('/', 1)[-1]

    return lastSpecificTopic

#init Alerta client :
alertaClient = Client(endpoint=ALERTA_ENDPOINT, key=ALERTA_API_KEY)

# Create MQTT client with websockets :
LOG.info ("démarrage du service MQTT -> ALERTA")
client_mqtt = mqtt.Client(protocol=mqtt.MQTTv5, transport="websockets", callback_api_version=CallbackAPIVersion.VERSION2)
if (MQTT_USE_TLS) :
    client_mqtt.tls_set()
client_mqtt.user_data_set({"alertaClient": alertaClient})     
# Add auth ids :
if MQTT_USERNAME_RO is not None and MQTT_PASSWORD_RO is not None :
    client_mqtt.username_pw_set(MQTT_USERNAME_RO, MQTT_PASSWORD_RO)

# set up callbacks :
client_mqtt.on_connect = on_connect
client_mqtt.on_message = on_message

# Connect to broker :
client_mqtt.connect(MQTT_HOST_URL,int(MQTT_HOST_PORT),60)
client_mqtt.loop_forever()


