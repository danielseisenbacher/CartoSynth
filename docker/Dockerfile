# CartoSynth runtime: Python + Inkscape (text to paths, rendering) + FontForge (custom fonts).
# Built and used by ./cartosynth.sh; also the VS Code devcontainer image.
FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        inkscape \
        fontforge \
        fontconfig \
        fonts-dejavu-core \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
COPY requirements.txt /tmp/requirements.txt
RUN uv pip install --system --no-cache -r /tmp/requirements.txt

# Fonts are read from the mounted repository (data/fonts/build, data/fonts/files),
# so nothing has to be installed as root and outputs belong to the calling user.
COPY docker/fonts.conf /etc/cartosynth/fonts.conf
ENV FONTCONFIG_FILE=/etc/cartosynth/fonts.conf \
    LANG=C.UTF-8 \
    PYTHONUTF8=1 \
    PYTHONUNBUFFERED=1

# non-root user for the devcontainer (./cartosynth.sh runs with your own uid instead)
RUN useradd --create-home --uid 1000 cartosynth
WORKDIR /workspace
