import uuid
from amrit_mqtt_publisher import publish_alert_message
from amrit_mqtt_publisher import publish_alert_messages, publish_alert_file
from amrit_mqtt_publisher.core.publisher import publish_simple_alert
from amrit_mqtt_publisher.models import Alert_raw


# ===== Send one alert =====
# Using a simple python dict
mock_alert_1 = {
  "resource": '1azqsqszaza',
  "event": 'Argo synthetic profile failure',
  "environment": 'Development',
  "severity": 'informational',
  "correlate": [],  
  "service": ['euro-argo'],
  "group": 'argo float alarm',
  "value": "0",
  "text": 'test alert',  
  "attributes": {
    "Country": 'Spain',          
    "alert_category": 'Data checker',          
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

publish_alert_message(mock_alert_1, "amrit/notification/raw/operations-alerts")
# # using the pydantic modele Aler_raw.Schema to build an alert object (from amrit_mqtt_publisher.models import Alert_raw)
# mock_alert_1b= Alert_raw.Schema(
#     resource='11zqsqsqsaz1b',
#     event='fake_alert',
#     environment='Development',
#     severity='informational',
#     correlate=[],
#     service=['euro-argo'],
#     group='argo float alarm',
#     value='0',
#     text='test alert',
#     attributes=Alert_raw.Attributes(
#         Country='spain',
#         alert_category='Data checker',
#         LastStationDate='24-05-2025',
#         url='https://fleetmonitoring.euro-argo.eu/float/5906990',
#         lastCycleNumberToRaiseAlarm='107'
#     ), # type: ignore
#     origin='test alert sender',
#     type='argo float alert demo',
#     timeout=120,
#     rawData=None
# ) # type: ignore
# publish_alert_message(mock_alert_1b, "amrit/notification/raw/operations-alerts")

# #send one alert by defining minimal attribute :
# publish_simple_alert(resource='11111c',event='fake_alert',service=['euro-argo'],alert_category=Alert_raw.AlertCategory.Information,severity=Alert_raw.Severity.informational)


# # ===== Send multiples alert =====
# mock_alert_2 = {
#   "resource": '2222',
#   "event": 'fake_alert',
#   "environment": 'Development',
#   "severity": 'informational',
#   "correlate": [],  
#   "service": ['euro-argo'],
#   "group": 'argo float alarm',
#   "value": "0",
#   "text": 'test alert',  
#   "attributes": {
#     "Country": 'Spain',          
#     "alert_category": 'Data checker',          
#     "ArgoType": 'PSEUDO',
#     "LastStationDate": '24-05-2025',
#     "url":'https://fleetmonitoring.euro-argo.eu/float/5906990',        
#     "lastCycleNumberToRaiseAlarm": '107',
#   },
#   "origin": 'test alert sender',
#   "type": 'argo float alert demo',        
#   "timeout": 120,
#   "rawData": None             
# }

# mock_alert_3 = {      
#     "resource": '33333',
#     "event": 'fake_alert',
#     "environment": 'Development',
#     "severity": 'informational',
#     "correlate": [],    
#     "service": ['euro-argo'],
#     "group": 'argo float alarm',
#     "value": "0",
#     "text": 'test alert',    
#     "attributes": {
#       "Country": 'Spain',          
#       "alert_category": 'Data checker',          
#       "ArgoType": 'PSEUDO',
#       "LastStationDate": '24-05-2025',
#       "url":'https://fleetmonitoring.euro-argo.eu/float/5906990',        
#       "lastCycleNumberToRaiseAlarm": '107',
#     },
#     "origin": 'test alert sender',
#     "type": 'argo float alert demo',        
#     "timeout": 120,
#     "rawData": None      
          
# }

# results = publish_alert_messages([mock_alert_2, mock_alert_3], "amrit/notification/raw/operations-alerts", stop_on_error=False)
# print(results)

# ===== Send alerts from file =====
# publish_alert_file("./demo_scripts/one_alert.json","amrit/notification/raw/operations-alerts" )

# results_file = publish_alert_file("./demo_scripts/two_alerts.json","amrit/notification/raw/operations-alerts",stop_on_error=False )
# print(results_file)