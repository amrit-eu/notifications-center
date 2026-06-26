FROM python:3.12-slim AS base

# Common base image.
LABEL org.opencontainers.image.authors="yvan.lubac@euro-argo"
LABEL org.opencontainers.image.description="Image containing all dependencies for amrit mqqt publisher library"
LABEL org.opencontainers.image.url="https://gitlab.ifremer.fr/amrit/development/notification-center/amrit-mqtt-publisher"
LABEL org.opencontainers.image.source="https://gitlab.ifremer.fr/amrit/development/notification-center/amrit-mqtt-publisher"
LABEL org.opencontainers.image.documentation="https://gitlab.ifremer.fr/amrit/development/notification-center/amrit-mqtt-publisher"
LABEL org.opencontainers.image.licenses="TBD"
LABEL org.opencontainers.image.vendor="Advance Marine Research Infrastructures Together (AMRIT)"

# Install Poetry for dependency management.
ENV POETRY_HOME=/opt/poetry
ENV PATH="${POETRY_HOME}/bin:${PATH}"

RUN \
    apt -y update && \
    apt -y install curl && \
    apt clean && \
    mkdir -p /opt/poetry/project /opt/poetry/bin && \
    curl -sSL https://install.python-poetry.org | python -

# Install dependencies.
COPY pyproject.toml poetry*.lock README.md /opt/poetry/project/
RUN \
    cd /opt/poetry/project && \
    poetry config virtualenvs.create false && \
    if [ ! -f poetry.lock ]; then poetry lock; fi && \
    poetry install --no-root && \
    poetry env info



FROM base AS build
# Ephemeral environment for building packages.
RUN --mount=type=bind,source=.,target=/opt/project,rw=true \
    cd /opt/project && \
    rm -rf ./dist && \
    poetry build && \
    mkdir /opt/build && \
    mv ./dist/*.whl /opt/build

FROM base AS app
# User-facing application environment.
RUN --mount=type=bind,from=build,source=/opt/build,target=/opt/build \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install /opt/build/*.whl && \
    /opt/venv/bin/python -c "from amrit_mqtt_publisher import publish_alert_message; print('OK')"

ENV PATH="/opt/venv/bin:${PATH}"
RUN useradd -ms /bin/bash mqttPublisherRunner
USER mqttPublisherRunner

WORKDIR /home/app



#overide entrypoint from base image
ENTRYPOINT ["/opt/venv/bin/python"]