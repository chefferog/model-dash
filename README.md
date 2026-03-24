# AI Model Dashboard

A lightweight web app that polls and displays the latest frontier model versions from major AI providers.

![Providers: Anthropic, OpenAI, Google, Meta, NVIDIA, Mistral](https://img.shields.io/badge/providers-6-blue)

## Features

- **Live model tracking** across Anthropic, OpenAI, Google, Meta, NVIDIA, and Mistral
- **Configurable polling** — hourly, twice daily, or daily
- **Manual refresh** with live status indicator
- **Responsive tile layout** — works on desktop and mobile
- **Graceful fallbacks** — shows last-known models if a provider is unreachable

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8080
```

Then open [http://localhost:8080](http://localhost:8080).

## Data Sources

| Provider  | Source |
|-----------|--------|
| Anthropic | Regex scrape of [docs.anthropic.com](https://docs.anthropic.com/en/docs/about-claude/models/all-models) |
| OpenAI    | Regex scrape of [platform.openai.com/docs/models](https://platform.openai.com/docs/models) |
| Google    | Regex scrape of [ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models) |
| Meta      | [Hugging Face public API](https://huggingface.co/api/models?author=meta-llama) — Llama models only |
| NVIDIA    | [NIM public catalog API](https://integrate.api.nvidia.com/v1/models) — `nvidia/*` models, Nemotron-first |
| Mistral   | BeautifulSoup table parse of [docs.mistral.ai](https://docs.mistral.ai/getting-started/models/overview/) |

> Most provider doc pages are JavaScript-rendered, so scrapers use regex on raw HTML rather than DOM parsing. All scrapers fall back to a curated static list if the live fetch fails.

## Project Structure

```
model-dash/
├── main.py          # FastAPI app — API routes + APScheduler background polling
├── scrapers.py      # Async scrapers for all 6 providers
├── config.json      # Persisted polling interval (written on change)
├── requirements.txt
└── static/
    ├── index.html
    ├── style.css
    └── app.js
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/models` | Latest cached model data + poll status |
| `GET` | `/api/config` | Current polling interval config |
| `PUT` | `/api/config` | Update polling interval (`hourly` / `twice_daily` / `daily`) |
| `POST` | `/api/refresh` | Trigger an immediate poll |

## Stack

- **Backend** — Python, FastAPI, httpx, BeautifulSoup4, APScheduler
- **Frontend** — Vanilla HTML/CSS/JS (no framework)
