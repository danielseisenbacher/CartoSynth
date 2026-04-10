FROM python:3.14-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    fontforge \
    inkscape\
    vim \
    git \
    locales-all \
 && rm -rf /var/lib/apt/lists/*

ENV LANG=de_DE.UTF-8
ENV LANGUAGE=de_DE:de
ENV LC_ALL=de_DE.UTF-8

RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

COPY requirements.in .
RUN uv pip install -r requirements.in