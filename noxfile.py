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


def uv_pip_install(session: nox.Session, *params: str):
    uv_env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    session.run("uv", "pip", "install", *params, env=uv_env, silent=True)


def uv_sync(session: nox.Session, *params: str):
    uv_env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    session.run("uv", "sync", *params, env=uv_env, silent=True)


PYPROJECT = nox.project.load_toml("pyproject.toml")
SUPPORTED_PYTHON_VERSIONS = nox.project.python_versions(PYPROJECT, max_version="3.12")


def parse_version(version: str) -> tuple[int, ...]:
    return tuple([int(it) for it in version.split(".")])


MINIMUM_PYTHON_VERSION = min(SUPPORTED_PYTHON_VERSIONS, key=parse_version)


@nox.session(venv_backend="uv", python=SUPPORTED_PYTHON_VERSIONS)
def test(session: nox.Session):
    uv_sync(session, "--group", "test")
    session.run(
        "pytest",
        "--cov",
        "--import-mode=importlib",
        "--doctest-modules",
        "tests",
        "--cov-report",
        "html",
        "--cov-report",
        "xml",
    )


@nox.session(venv_backend="uv", python=MINIMUM_PYTHON_VERSION)
def depcheck(session: nox.Session):
    uv_sync(session, "--group", "depcheck")
    session.run("deptry", "src/", "tests/")


@nox.session(venv_backend="uv", python=MINIMUM_PYTHON_VERSION)
def check_format(session: nox.Session):
    uv_pip_install(session, "--group", "format")
    session.run("ruff", "format", "--check")
    session.run("ruff", "check", "--select", "I")


@nox.session(venv_backend="uv", python=MINIMUM_PYTHON_VERSION)
def typecheck(session: nox.Session):
    uv_sync(session, "--group", "typecheck")
    session.run("pyright", "src/", "tests/")


@nox.session(venv_backend="uv", python=MINIMUM_PYTHON_VERSION)
def lint(session: nox.Session):
    uv_sync(session, "--group", "lint")
    session.run("ruff", "check")


@nox.session(venv_backend="uv", default=False, python=MINIMUM_PYTHON_VERSION)
def apply_format(session: nox.Session):
    uv_pip_install(session, "--group", "format")
    session.run("ruff", "format")
    session.run("ruff", "check", "--fix", "--select", "I")


@nox.session(venv_backend="uv", default=False, python=MINIMUM_PYTHON_VERSION)
def fix(session: nox.Session):
    uv_sync(session, "--group", "lint")
    session.run("ruff", "check", "--fix")


@nox.session(venv_backend="uv", default=False, python=MINIMUM_PYTHON_VERSION)
def build(session: nox.Session):
    session.run("uv", "build", ".")


@nox.session(venv_backend="uv", default=False, python=MINIMUM_PYTHON_VERSION)
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


DOCKER_UP_ENV = {
    "CONVERSATIONAL_AGENT_API_PORT": "5020",
    # "KAFKA_BROKER_PORT": "9094",
}


# @nox.session(default=False, python=False)
# def docker_up(session: nox.Session):
#     session.run(
#         "docker",
#         "compose",
#         "-p",
#         "conversational_agent",
#         "-f",
#         "deployment/docker-compose/dev.yml",
#         "-f",
#         "deployment/docker-compose/dependencies.yml",
#         "up",
#         "--build",
#         *session.posargs,
#         external=True,
#         env={**DOCKER_UP_ENV},
#     )


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


@nox.session(default=False, python=False)
def env_file(session: nox.Session):
    parser = argparse.ArgumentParser(description="Set up your dev environment for this repo")
    parser.add_argument(
        "--overwrite-env-file",
        help="Overwrite .env file if it exists",
        default=False,
        action=argparse.BooleanOptionalAction,
    )
    args, unknown = parser.parse_known_args(args=session.posargs)
    env_path = Path(os.getcwd(), ".env")
    env_file = dedent("")

    if not env_path.exists() or args.overwrite_env_file:
        session.log("Creating .env file at %s", env_path)
        with env_path.open("w"):
            env_path.write_text(env_file)
    else:
        session.log(
            "Not creating .env file because it already exists and --overwrite-env-file is not set. Default content:\n%s",
            env_file,
        )


if __name__ == "__main__":
    nox.main()
