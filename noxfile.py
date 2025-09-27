#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "nox",
#   "uv >0.6,<0.7",
#   "docker",
#  ]
# ///

import argparse
import os
from pathlib import Path
from textwrap import dedent

import nox


@nox.session(venv_backend="uv", default=False, python="3.12")
def generate_openapi_spec(session: nox.Session):
    parser = argparse.ArgumentParser(description="Generate an OpenAPI spec")
    parser.add_argument(
        "--output",
        type=Path,
        help="The file to output the spec to",
    )
    args: argparse.Namespace = parser.parse_args(args=session.posargs)
    output: Path = args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    uv_env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    session.run_install("uv", "pip", "install", os.getcwd(), env=uv_env)
    session.run(
        "python",
        "-c",
        dedent(f"""\
            import json
            from conversational_agent.core.api.endpoints import app
            with open("{output}", "w") as fd:
                json.dump(app().openapi(), fd)
            """),
    )


@nox.session(default=False, python=False)
def docker_build(session: nox.Session):
    session.run(
        "docker", "compose", "-f", "deployment/docker-compose/build.yml", "build", external=True
    )


@nox.session(default=False, python=False)
def docker_up(session: nox.Session):
    # ALWAYS build first to ensure image is up-to-date
    docker_build(session)
    session.run(
        "docker",
        "compose",
        "-p",
        "conversational_agent",
        "-f",
        "deployment/docker-compose/application.yml",
        "up",
        external=True,
    )


# @nox.session(default=False, python=False)
# def docker_down(session: nox.Session):
#     session.run(
#         "docker",
#         "compose",
#         "-p",
#         "conversational_agent",
#         "-f",
#         "deployment/docker-compose/dev.yml",
#         "-f",
#         "deployment/docker-compose/dependencies.yml",
#         "down",
#         *session.posargs,
#         external=True,
#     )

if __name__ == "__main__":
    nox.main()
