#!/bin/bash
set -e

# Attendre que l’entrypoint officiel ait généré supervisord.conf
bash /usr/local/bin/docker-entrypoint.sh

# creation d'une API KEY READ ONLY pour le dashboard amrit
ADMIN_USER=${ADMIN_USERS%%,*}
if [ -n "${ALERTA_READ_API_KEY}" ]; then
    echo "# Create user-defined API key read-only."
    alertad key --username "${ADMIN_USER}" --key "${ALERTA_READ_API_KEY}" --scope read:alerts --scope read --duration "315360000" --text "read key for AMRIT Dashboard"
fi

# Append conf du service mqtt
cat /app/mqtt_service.conf >> /app/supervisord.conf

# Lancer supervisord
exec supervisord -c /app/supervisord.conf


