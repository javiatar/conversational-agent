# Conversational Agent

This repository contains the 'Conversational Agent' take home exercise.

## Usage Tutorial: Set up your environment to work with this repo
Set up env via:

1. Open this repo in a new VSCode workspace:
    ```sh
    code relative/path/to/this/repo
    ```

1. Create and source a venv
    ```sh
    uv venv
    source .venv/bin/activate
    ```

1. Install project dependencies on that venv from `pyproject.toml`:
    ```sh
    uv sync --active --group dev
    ```

## Usage Tutorial: Spinning up your new Conversational Agent Application
Below we'll go over how to use docker and curl to create the Conversational Agent Application's container images, spin them up, and issue requests to those containers' API endpoints to see the bricks backend in action. To bypass docker and run your modules
directly (e.g during development) skip to the Local Development section below.

1. Create the docker container images for the Conversational Agent application.
    ```sh
    uvx nox -s docker_build
    ```

2. Spin up your built application containers, including an API container that will expose a set of endpoints to interface with the conversational agent.
    ```sh
    uvx nox -s docker_up
    ```

3. In a new terminal, issue a request to the Conversational Agent Application's API endpoint, exposed by default on port 5020:
    ```sh
    curl localhost:5020/health | jq
    ```
      - Expecting: `{"status":"ok!"}`

4. Peruse other endpoints provisoned on your API by going to `http://localhost:5020/docs` on your browser

### Local Development
If you want to test running your application outside a docker container, you can do that like so:

1. Check that you don't have another instance of your app running

1. Ensure that you're running in a virtual environment with your dependencies installed

2. In a terminal, run the following:
    ```sh
    python3 -m uvicorn conversational_agent.api.endpoints:app --host 0.0.0.0 --port 5020
    ```

3. In a separate terminal, you may issue requests to [all available endpoints](http://localhost:5020/docs), as explained above, like so:
    ```sh
    curl localhost:5020/health | jq
    ```
    - Expecting: `{"status":"ok!"}`