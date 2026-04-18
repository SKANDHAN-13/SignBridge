# syntax=docker/dockerfile:1.6
FROM --platform=linux/arm64 ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    python3-opencv \
    python3-tk \
    espeak-ng \
    portaudio19-dev \
    pulseaudio libpulse0 libpulse-dev \
    alsa-utils \
    build-essential pkg-config \
    git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements-core.txt requirements-gpio.txt requirements.txt ./

RUN python3 -m pip install --break-system-packages -r requirements-core.txt

# Optional GPIO (won't fail the build if not available in this environment)
RUN python3 -m pip install --break-system-packages -r requirements-gpio.txt || true

COPY . .

CMD ["python3", "main.py"]
