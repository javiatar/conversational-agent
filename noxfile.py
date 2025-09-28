#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "nox",
#   "uv >0.6,<0.7",
#   "docker",
#  ]
# ///


import nox

PYPROJECT = nox.project.load_toml("pyproject.toml")


def uv_sync(session: nox.Session, *params: str):
    uv_env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    session.run("uv", "sync", *params, env=uv_env, silent=True)


@nox.session()
def test(session: nox.Session):
    uv_sync(session, "--group", "test")
    session.run("pytest", ".")


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


@nox.session(default=False, python=False)
def docker_down(session: nox.Session):
    session.run(
        "docker",
        "compose",
        "-p",
        "conversational_agent",
        "-f",
        "deployment/docker-compose/application.yml",
        "down",
        external=True,
    )


if __name__ == "__main__":
    nox.main()
