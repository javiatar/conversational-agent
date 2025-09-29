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
   - Copies the application code

2. **PostgreSQL Container**:
   - Starts on port 5432
   - Creates database `conversational_agent_db`
   - User: `admin`, Password: `admin`
   - Data persists in Docker volume `postgres-data`

3. **API Container**:
   - Starts on port 5020
   - Mounts local `storage/` directory for RAG indexes
   - Connects to PostgreSQL container via internal networking
   - Initializes database tables on startup

## System Architecture Overview

### High-Level Architecture

```bash
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│   FastAPI       │───▶│   PostgreSQL    │
│   Client        │    │   Application   │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   OpenAI        │    │   RAG Service   │
                       │   LLM Service   │───▶│   (Pyserini)    │
                       └─────────────────┘    └─────────────────┘
```

### Core Components

1. **API Layer** (`src/conversational_agent/api/`)
   - **FastAPI application** with CORS middleware for cross-origin requests
   - **Agent router** handling authentication, conversation management, and chat endpoints
   - **OpenAPI documentation** at `/docs` endpoint (out-of-the-box by FastAPI)

1. **Services Layer** (`src/conversational_agent/services/`)
   - **Agent Service**: User authentication, conversation initialization, and customer management
   - **LLM Service**: OpenAI GPT integration with structured output parsing for issue triage
   - **RAG Service**: Document retrieval using Pyserini/Lucene for context-aware responses

1. **Data Layer** (`src/conversational_agent/data_models/`)
   - **Database Models**: SQLModel entities for Customer, Conversation, Turn, Issue with proper relationships
   - **API Models**: Pydantic request/response schemas for endpoint validation and strong type constraints
   - **ML Models**: OpenAI structured output format and system prompts for consistent LLM behavior

1. **Configuration** (`src/conversational_agent/config/`)
   - **Database**: AsyncSession management with PostgreSQL connection pooling
  - **OpenAI**: API key management and model configuration
  - **RAG**: Index paths, knowledge base settings, and search parameters

1. **Knowledge Base & Search** (`src/conversational_agent/scripts/` | `storage`)
   - **JSONL knowledge base** containing made-up customer service policies and procedures
   - **Index-building scripts** pipeline for building knowledge base and sparse search indexes

1. **Fake CLI-based front-end** (`src/frontend`)
   - **CLI-based Frontend** allows visualisation of the API endpoint behaviour (bot chats and summary)

## Key Design Decisions

1. **Singleton Pattern for Services**: Ensures single instances of expensive resources (DB connections, LLM clients, RAG indexes) or conflict-prone config (DBConfig). Implemented custom `@singleton` decorator to prevent duplicate initialization of a decorated callable
1. **Structured LLM Output with Pydantic**: Ensures consistent, typed responses from OpenAI for reliable issue triage. Implemented `OpenAIAPIIssueFormat` model with progressive field completion ensuring we progressively extracted necessary DB fields while incorporating an `assistant_reply` for the model to continue the conversation.
1. **RAG Integration with Pyserini**: Pyserini allows same-process RAG functionality to complement and ground model answers. Implemented via sparse BM25 search with up-to-date context injection into system prompt. (Unfortunately poor typing makes working with returned java-wrapper Document awkward)
1. **Async/Await Throughout**: Non-blocking I/O for database operations, OpenAI API calls, and concurrent request handling
1. **Docker Multi-Stage Architecture**: Optimized production images with proper dependency management. Separated containers for API and database with shared volumes for easy scaling, deployment and development environment consistency
1. **Nox for Build Automation**: Consistent, reproducible build and deployment processes including common CI/CD steps for a production pipeline and faster developer oboarding.

## Potential improvements

1. **Dense Vector Search**: Add FAISS/embedding-based retrieval alongside BM25 for semantic search
2. **Conversation Memory Checkpoints**: Summarize conversation every X-turns for handling long contexts
3. **Few-shot grounding examples**: Provide few-shot examples to ground behaviour (e.g when to determine a user's intent is to close conversation vs to escalate to a human)
4. **Kafka for partition tolerance**: Add a Kafka cluster to handle ongoing conversations with multiple API/Agent copies to resume under failure
5. **MCP-Driven Intelligent RAG**: Use Model Context Protocol with LLM reasoning to dynamically decide when to invoke RAG retrieval based on query intent and context needs
