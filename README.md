# EvalWise

A developer-friendly red teaming and evaluation platform for Large Language Models (LLMs).

## Features

- **Evaluations**: Built-in evaluators including LLM judges with ISO 42001 and EU AI Act rubrics
- **Red Teaming**: Basic jailbreak scenarios and adversarial testing
- **Datasets**: CSV/JSONL upload with version tracking
- **Metrics**: Pass rates, mean scores, and run comparisons
- **Playground**: Single prompt testing with immediate evaluation
- **Multi-Provider**: Support for OpenAI, Azure OpenAI, and OpenAI-compatible endpoints

## Quick Start

```bash
# Start development environment
make dev

# Run complete demo
make demo

# Access the application
# Web UI: http://localhost:3000
# API docs: http://localhost:8000/docs
```

## Requirements

- Docker & Docker Compose
- Make

## Architecture

- **Backend**: FastAPI + PostgreSQL + Redis
- **Workers**: Celery for async evaluation jobs
- **Frontend**: Next.js 15 + TypeScript + TailwindCSS
- **Evaluators**: Local inference with transformers and sentence-transformers
- **Retention**: Automatic 90-day data purge

## License

AGPLv3