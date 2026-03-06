
import contextlib
import time

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from ..config import get_config


class _MqttPublisher :
  """Internal class.
  MQTT publisher using Paho MQTT over secure WebSockets.
    - Builds a TLS-enabled WebSocket MQTT client
    - Configures username/password from environment variables
    - Connects on demand  and waits until the connection is established
    - Publishes messages to a given topic
    - Exposes a simple `disconnect()` method to stop the loop and close the connection

  Requirements (expected to be defined elsewhere in your code):
    - Environment variables: MQTT_USERNAME_RW, MQTT_PASSWORD_RW
    - Constants/variables:   MQTT_HOST_URL, MQTT_HOST_PORT

  Parameters
  ----------
  name : str, optional
      Optional logical name for this publisher instance (not used directly here).
      Can be useful to tag logs or to build a custom client-id if you extend the class.

  Attributes
  ----------
  client : paho.mqtt.client.Client
      Underlying Paho MQTT client configured for secure WebSockets.
  clientConnected : bool
      Tracks whether the broker connection has been established (set by `on_connect`).

  Methods
  -------
  publish(message: str, topic: str) to publish a message on the mqtt.

  """

  def __init__(self, name=None):  
        """Initialize the MQTT client, configure TLS and authentication, and register callbacks.

        Notes
        -----
        - This constructor only prepares the client; it does not connect immediately.
          The connection is established when `publish()` calls `self.connect()` (lazy connect).
        - The username/password must be available in the current process environment
          (e.g., exported in your shell or set via your launcher script).

        """
        cfg = get_config()
        if not cfg.mqtt_host:
            raise RuntimeError("no MQTT host defined")
        if not cfg.mqtt_port:
            raise RuntimeError("no MQTT port defined")

        
        # Create MQTT client with websockets :
        self.client = mqtt.Client(protocol=mqtt.MQTTv5, transport="websockets", callback_api_version=CallbackAPIVersion.VERSION2, client_id=cfg.client_id)
        if (cfg.mqtt_tls):
          self.client.tls_set()        

        # Add auth ids :
        if cfg.mqtt_username is not None and cfg.mqtt_password is not None:
          self.client.username_pw_set(cfg.mqtt_username, cfg.mqtt_password)

        # set up callbacks :
        self.client.on_connect = self._on_connect
        
        self.clientConnected = False

  # Callback when connection with MQTT broker is done
  def _on_connect ( self, client, userdata, flags, rc, properties=None):
      """Paho callback invoked when the client finishes the CONNECT handshake.

      - On success (rc == 0), logs an info message and flips `self.clientConnected` to True.
      - On failure, aborts the program with an explicit error message (via exitWithError).

      Notes
      -----
      - Common rc values:
          0: Connection Accepted
          4: Bad username or password
          5: Not authorized
        Check broker logs/ACL if you receive 4 or 5.

      """
      if rc == 0:
          self.clientConnected=True
      else :
          raise RuntimeError(f"Connection with MQTT has failed, error code : {rc}")

  def publish (self, message, topic, retain: bool = False) :
      """Publish a message to a given topic, connecting first if needed.

      Parameters
      ----------
      message : str or bytes
          The payload to publish.
      topic : str
          The MQTT topic to publish to.
      retain : bool, optional
        Whether to retain messages on the broker (default: False).
        
      Behavior
      --------
      - Ensures the client is connected.
      - Publishes and checks the return code.
      - Logs errors via `xmlReport.addError` if publish fails or raises.

      """
      # Connect to broker if not connected :
      self.connect()
      # publish message :
      try :
          publishResult = self.client.publish(topic, message, retain=retain)
          if publishResult.rc != 0:
            raise RuntimeError (f"Failed to publish message to MQTT. Return code: {publishResult.rc}")
      except Exception:         
        raise RuntimeError (f"Unexpected error when trying to publish to MQTT: {publishResult.rc}")
        
  def connect (self) :
      """Ensure the client is connected to the MQTT broker (lazy connect with timeout) and connect if not.
      """
      if self.clientConnected:
            return
      cfg = get_config()                  
      try :
        self.client.connect(cfg.mqtt_host,cfg.mqtt_port,keepalive=60)
        self.client.loop_start()      
        # wait to be connected to MQTT before trying to publish
        timeout = time.time() + 5  # max 5s
        while not self.clientConnected:
            if time.time() > timeout:
                raise TimeoutError("Timeout waiting for MQTT connection")
            time.sleep(0.1)
      except Exception as connexion_error :
        with contextlib.suppress(Exception):
          self.client.loop_stop()
          self.client.disconnect()
        raise RuntimeError(f"MQTT connection error: {connexion_error}")          


  def disconnect (self) :
      """Stop the network loop and disconnect from the MQTT broker.
      """
      self.client.loop_stop()
      self.client.disconnect()
      self.clientConnected = False