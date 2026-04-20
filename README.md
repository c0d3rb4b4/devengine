# DevEngine

DevEngine is a starter scaffold for a self-hosted platform that gives AI agents structured ownership over software repositories.

The long-term goal is not just "an LLM that opens pull requests." The idea is to build a durable system that can continuously understand a codebase, accept work, plan changes, implement them in bounded steps, run CI, recover from failures, and keep improving the repository over time.

In other words, DevEngine is intended to become a practical operating layer for autonomous software development and maintenance.

## Motive

Most AI coding setups today are still session-based. They can help write code, review a patch, or answer questions, but they do not really *own* the ongoing development loop of a project.

DevEngine exists to close that gap.

The platform is meant to support workflows such as:

- taking in a GitHub issue as the source of truth for new work
- generating design notes and phased implementation plans
- executing work in isolated branches or workspaces
- running tests and CI
- analyzing failures and retrying within safe limits
- maintaining project context over time instead of starting from zero each session
- eventually supporting multiple repositories with shared infrastructure but isolated execution

The aim is to stay honest and engineering-focused. This is not pitched as fully magical autonomous software creation. It is a structured system for letting AI do more of the repetitive, traceable, operational parts of repository ownership while still leaving room for human control where it matters.

## Current state

This repository is an early scaffold for that larger platform.

Right now it provides the local foundation you can run on a VM, for example on Proxmox, with a single bootstrap flow. It gives you the services and file layout needed to start wiring in webhook intake, orchestration, state management, repo workspaces, and optional public tunnelling.

## What it includes

- FastAPI webhook and API service
- LangGraph smoke-test graph and orchestration skeleton
- Postgres for durable state
- Optional Redis cache and queue service
- Runner container for repo workspaces and helper scripts
- Optional ngrok sidecar for exposing the webhook publicly
- Docker Compose based startup
- VM bootstrap helper script for Ubuntu

## Repo layout

```text
devEngine/
  api/                    # FastAPI app
  agent/                  # LangGraph code and orchestration skeleton
  runner/                 # repo execution helpers
  config/                 # editable configuration files
  scripts/                # bootstrap and health scripts
  postgres/init/          # optional SQL init scripts
  workspace/              # checked out repos live here
  logs/                   # local file logs if you want them
  secrets/                # place private keys here locally
  docker-compose.yml
  bootstrap.sh
  teardown.sh
  .env.example
```

## Architecture in plain English

### API

The FastAPI service is the front door. It receives webhooks, exposes health endpoints, and can later become the place where runs are created, inspected, paused, or resumed.

### Agent

The agent service is where LangGraph sits. LangGraph is not a system package or infrastructure daemon. It is the orchestration layer inside the Python application that owns workflow state and decides what happens next.

Over time this is the part that can coordinate:

- issue intake
- design generation
- phase planning
- implementation loops
- CI monitoring
- bounded autofix retries
- escalation when a circuit breaker trips

### Runner

The runner service is where actual repository work can happen in isolated workspaces. In a fuller version, this is the place that clones repos, creates branches, runs tests, applies changes, and pushes results.

### Data services

Postgres gives the platform durable state. Redis is optional and can later help with queues, caching, and concurrency controls.

### Tunnel

ngrok is included as an optional convenience so GitHub can reach your webhook during local or homelab trials.

## Quick start

### 1) One-time VM prep

On Ubuntu 24.04:

```bash
chmod +x scripts/bootstrap_vm.sh
./scripts/bootstrap_vm.sh
```

Log out and back in after Docker group membership is applied.

### 2) Configure the project

```bash
cp .env.example .env
mkdir -p secrets
```

Edit `.env` and `config/repos.json`.

Put your GitHub App private key PEM file at:

```text
secrets/github-app.pem
```

### 3) Start the stack

```bash
chmod +x bootstrap.sh teardown.sh scripts/*.sh
./bootstrap.sh
```

### 4) Check health

```bash
./scripts/check_health.sh
```

## Services

### API

FastAPI service exposing:

- `GET /health`
- `POST /github/webhook`
- `GET /debug/config`

### Agent

Contains a tiny LangGraph smoke test and a skeleton task orchestrator.

### Runner

Contains placeholder helpers for:

- repo cloning
- branch creation
- local workspace isolation
- CI log analysis hooks

## Configuration

### `.env`

Holds local runtime settings and secrets references such as:

- GitHub App identifiers
- webhook secret
- database connection string
- workspace root
- ngrok token
- default base branch
- retry limits

### `config/repos.json`

Holds per-repo settings so the platform can eventually support multiple repositories without duplicating infrastructure.

### `config/app.toml`

Holds local application defaults for agent and runner behaviour.

## ngrok

If `ENABLE_NGROK=true` and `NGROK_AUTHTOKEN` is set in `.env`, the ngrok service starts alongside the stack.

You can then use the public URL it prints for your GitHub App webhook.

## Important notes

- Real secrets are **not** committed.
- `.env` is local only.
- `secrets/` is local only.
- This scaffold is intentionally safe and does not auto-modify any target repo yet.
- The included LangGraph code is a smoke-test and skeleton, not the finished autonomous platform.

## Where this can grow next

Once the stack is up, the next layers to add are:

1. GitHub App installation token generation
2. Issue intake and filtering
3. Real task persistence in Postgres
4. Repo execution against isolated workspaces
5. CI polling and bounded autofix loops
6. Multi-repo scheduling and concurrency control
7. Model routing so different LLMs can handle design, coding, or log analysis
8. Optional human escalation paths for high-risk work

## Development philosophy

DevEngine is meant to stay practical.

That means:

- workflows should be explicit
- state should be durable and inspectable
- repo execution should be isolated
- retries should be bounded
- the system should fail safely
- human control should remain available without being required for every small change

The goal is not hype. The goal is to build a platform that can genuinely take on more repository ownership over time without becoming opaque or reckless.
