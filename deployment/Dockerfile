ARG BASE_IMAGE

FROM ${BASE_IMAGE:-"python:3.12-slim-bookworm"} AS build-env

# Copy the entire source code for the project installation
COPY . /src
WORKDIR /src

RUN apt-get update && apt-get install -y pip && \
    pip install uv

# Install torch and related dependencies in a separate stage to leverage caching
RUN uv sync --active --group dev
# Install the project itself
RUN uv pip install --no-deps /src