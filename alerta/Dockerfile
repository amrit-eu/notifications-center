FROM alerta/alerta-web


# JWT AUTH - Remplace directement dans le container les fichiers modifiés pour les besoins de l'auth amrit par jeton JWT :
COPY amrit_custom_alerta_patch/alerta/auth/__init__.py /venv/lib/python3.9/site-packages/alerta/auth/__init__.py
COPY amrit_custom_alerta_patch/alerta/auth/bearer.py    /venv/lib/python3.9/site-packages/alerta/auth/bearer.py
COPY amrit_custom_alerta_patch/alerta/utils/config.py    /venv/lib/python3.9/site-packages/alerta/utils/config.py
# Changement de l'action réalisé lorsqu'une alerte est expirée 
COPY amrit_custom_alerta_patch/alerta/models/alert.py   /venv/lib/python3.9/site-packages/alerta/models/alert.py
COPY amrit_custom_alerta_patch/alerta/database/backends/postgres/base.py   /venv/lib/python3.9/site-packages/alerta/database/backends/postgres/base.py
#ajout endpoint alerts/events pour la liste des event
COPY amrit_custom_alerta_patch/alerta/database/base.py   /venv/lib/python3.9/site-packages/alerta/database/base.py
COPY amrit_custom_alerta_patch/alerta/views/alerts.py   /venv/lib/python3.9/site-packages/alerta/views/alerts.py
# ajoute un fix non encore mergé sur la branche principale : https://github.com/alerta/alerta/pull/2020
COPY amrit_custom_alerta_patch/alerta/database/backends/postgres/queryparser.py   /venv/lib/python3.9/site-packages/alerta/database/backends/postgres/queryparser.py 
# Modification du core plugin'reject' pour que les alertes ne respecant pas le format amrit soient rejetées par Alerta:
COPY amrit_custom_alerta_patch/alerta/plugins/reject.py /venv/lib/python3.9/site-packages/alerta/plugins/reject.py
COPY amrit_custom_alerta_patch/alerta/plugins/models /venv/lib/python3.9/site-packages/alerta/plugins/models

#ALERTA -> MQTT PLUGIN ajoute et install le plugin MQTT : alerta -> MQTT
COPY ./plugins/mqtt /tmp
WORKDIR /tmp
RUN /venv/bin/pip install .



#MQTT -> Alerta SERVICE:
COPY mqtt_to_Alerta_service /app/mqtt_to_Alerta_service
WORKDIR /app/mqtt_to_Alerta_service
RUN /venv/bin/pip install -r requirements.txt
COPY mqtt_service.conf /app/mqtt_service.conf
USER root
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
USER 1001
ENTRYPOINT ["/app/entrypoint.sh"]