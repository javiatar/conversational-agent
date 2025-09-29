# Conversational Agent

This repository contains a conversational agent service that provides intelligent customer support with RAG (Retrieval-Augmented Generation) capabilities. The agent can triage customer issues, extract relevant information, and provide contextually aware responses using a knowledge base.

## TL;DR - Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/javiatar/conversational-agent.git
   cd conversational-agent
   ```

2. Create `.env` file with your OpenAI API key:
   ```bash
   echo 'export OPENAI_API__KEY="your-openai-api-key-here"' > .env
   ```

3. Install uvx (if you don't have it):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or
   pip install uvx
   ```

4. Start the application:
   ```bash
   uvx nox -s docker_up
   ```

5. Test the API:
   ```bash
   # Run the interactive 'fake' CLI frontend:
   python src/frontend/frontend.py
   ```

The API will be available at `http://localhost:5020` with documentation at `/docs`.

## Detailed Setup Instructions

### Prerequisites

- **Docker & Docker Compose**: For containerized deployment
- **uvx**: Python package runner (installs automatically with uv)
- **OpenAI API Key**: Required for LLM functionality

### Architecture Overview

This application uses Docker Compose to orchestrate multiple services:

- **API Container**: FastAPI application with the conversational agent
- **PostgreSQL Container**: Database for storing conversations, customers, and issues
- **Shared Volumes**: For RAG knowledge base and indexes

### Environment Configuration

Create a `.env` file in the root directory with the following variables:

```bash
# Required: OpenAI API key for LLM functionality
export OPENAI_API__KEY="your-openai-api-key-here"
# Required: Database connection URL (points to Docker PostgreSQL container)
export DB_CONFIG__URL="postgresql+psycopg://admin:admin@postgres:5432/conversational_agent_db"
# Optional: Enable RAG (Retrieval-Augmented Generation) for enhanced responses
export RAG__ENABLED=True # Default is False
```

### Step-by-Step Installation

1. Clone and navigate to the repository, install uvx, and create `.env` file as above

   ```bash
   git clone https://github.com/javiatar/conversational-agent.git
   cd conversational-agent
   ```

1. Build and start all services:

   ```bash
   # This command will:
   # - Build the Docker image with all dependencies
   # - Start PostgreSQL database container
   # - Start the API container
   # - Set up networking between containers
   uvx nox -s docker_up
   ```

1. Verify the installation:

   ```bash
   # Check API health
   curl http://localhost:5020/health
   # visit http://localhost:5020/docs in your browser
   ```

### What Gets Started

When you run `uvx nox -s docker_up`, the following happens:

1. **Docker Image Build**: 
   - Installs Python 3.12 and dependencies
   - Installs Java 21 (required for RAG/Pyserini)
   - Copies your application code

1. **PostgreSQL Container**:
   - Starts on port 5432
   - Creates database `conversational_agent_db`
   - User: `admin`, Password: `admin`
   - Data persists in Docker volume `postgres-data`

1. **API Container**:
   - Starts on port 5020
   - Mounts local `storage/` directory for RAG indexes
   - Connects to PostgreSQL container via internal networking
   - Initializes database tables on startup
