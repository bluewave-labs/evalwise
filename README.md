# EvalWise

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15+-000000?logo=nextdotjs)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791?logo=postgresql)](https://postgresql.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

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
# Web UI: http://localhost:3001
# API docs: http://localhost:8003/docs
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