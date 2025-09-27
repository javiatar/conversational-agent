ARG BASE_IMAGE

FROM ${BASE_IMAGE:-"python:3.12-slim-bookworm"} AS common-env

# Use standard site-packages location for all dependencies installed.
ENV TARGET_DIR=/site-packages
# Standardise UV cache location.
ENV UV_CACHE_DIR=/root/.cache/uv

FROM common-env AS base

# Copy pyproject.toml for dependency resolution
COPY pyproject.toml /src/
WORKDIR /src

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=${UV_CACHE_DIR} \
    # Compile pyproject.toml to get the project requirements (excludes system site packages)
    uv pip compile pyproject.toml -o /var/project-requirements.txt

FROM common-env AS deps-install

COPY --from=base /var/project-requirements.txt /var/project-requirements.txt

# Install dependencies
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=${UV_CACHE_DIR} \
    uv pip install --no-deps -r /var/project-requirements.txt --target=${TARGET_DIR}

FROM common-env AS project-build

# Copy the entire source code for the project installation
COPY . /src
WORKDIR /src

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=${UV_CACHE_DIR} \
    uv pip install --no-deps /src --target=${TARGET_DIR}

# Build from base to avoid pulling any build-time config into final image
FROM ${BASE_IMAGE:-"python:3.12-slim-bookworm"} AS run
# Use standard site-packages location for all dependencies installed.
ENV TARGET_DIR=/site-packages
# Ensure python searches for modules in our custom site-packages directory
ENV PYTHONPATH=${TARGET_DIR}

# Copy the TARGET_DIR from each of the previous stages into this image
COPY --from=deps-install ${TARGET_DIR}/. ${TARGET_DIR}/.
COPY --from=project-build ${TARGET_DIR}/. ${TARGET_DIR}/.