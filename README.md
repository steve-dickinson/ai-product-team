# ai-product-team

Automated AI Product R&D Team — multi-agent product discovery and development pipeline.

## Features
- Multi-agent ideation, evaluation, and debate
- Persistent memory with MongoDB and Redis (via Docker)
- Orchestrated pipeline with phase gates and cost/safety monitoring
- Modular stages (stage_1.py ... stage_6.py) for stepwise exploration
- Rich CLI output (via `rich`)

## Quickstart

### 1. Clone and install dependencies
```bash
git clone <repo-url>
cd ai-product-team
uv pip install -r requirements.txt  # or use your preferred Python 3.12+ environment
```

### 2. Configure environment
Copy `.env` and set your API keys and infrastructure variables:
```bash
cp .env.example .env  # if provided, else edit .env directly
# Edit .env to set ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.
```

### 3. Start infrastructure (MongoDB & Redis)
```bash
docker compose up -d
```
MongoDB will be available on port 27018, Redis on 6379.

### 4. Run a stage
```bash
uv run python stage_1.py
uv run python stage_2.py
# ... up to stage_6.py
```

### 5. Run tests
```bash
uv run pytest tests/ -v
```

## Project Structure
- `stage_1.py` ... `stage_6.py`: Progressive pipeline stages
- `src/`: Core source code (agents, core logic, storage, models)
- `docker-compose.yml`: Local MongoDB/Redis setup
- `.env`: Environment variables (API keys, DB URIs, etc.)
- `tests/`: Unit and integration tests

## Configuration
Edit `.env` to set your API keys and DB connection info. Example:
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
MONGODB_URI=mongodb://admin:changeme_mongo_pwd@localhost:27018
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Requirements
- Python 3.12+
- Docker (for MongoDB/Redis)
- API keys for Anthropic and OpenAI

## License
MIT