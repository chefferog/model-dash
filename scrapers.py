import asyncio
import re
from bs4 import BeautifulSoup
import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

TIMEOUT = 20


# ── Anthropic ──────────────────────────────────────────────────────────────────
async def fetch_anthropic():
    url = "https://docs.anthropic.com/en/docs/about-claude/models/all-models"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as c:
            r = await c.get(url, headers=HEADERS)
            r.raise_for_status()

        # The page embeds model IDs in the JS bundle — regex on raw HTML is most reliable
        text = r.text
        # Match versioned model IDs (contain a date stamp or version suffix)
        raw = re.findall(r"claude-(?:opus|sonnet|haiku|instant|claude)[\w.-]*", text, re.IGNORECASE)

        skip = {"claude-code-", "claude-in-", "claude-on-", "claude-api"}
        seen_bases, models = set(), []
        for mid in raw:
            mid = mid.rstrip(".,/\"'")
            if any(mid.startswith(s) for s in skip):
                continue
            # Normalise: strip trailing -v\d+ alias so we don't show duplicates
            base = re.sub(r"-v\d+$", "", mid)
            if base not in seen_bases and len(base) > 8:
                seen_bases.add(base)
                models.append({"id": base, "name": base})

        # Sort by date stamp desc (newer first)
        def sort_key(m):
            match = re.search(r"(\d{8})", m["id"])
            return match.group() if match else "0"

        models.sort(key=sort_key, reverse=True)
        return models[:8] if models else _fallback_anthropic()
    except Exception:
        return _fallback_anthropic()


def _fallback_anthropic():
    return [
        {"id": "claude-opus-4-6",              "name": "Claude Opus 4.6"},
        {"id": "claude-sonnet-4-6",             "name": "Claude Sonnet 4.6"},
        {"id": "claude-haiku-4-5-20251001",     "name": "Claude Haiku 4.5"},
        {"id": "claude-3-5-sonnet-20241022",    "name": "Claude 3.5 Sonnet"},
        {"id": "claude-3-5-haiku-20241022",     "name": "Claude 3.5 Haiku"},
        {"id": "claude-3-opus-20240229",        "name": "Claude 3 Opus"},
    ]


# ── OpenAI ─────────────────────────────────────────────────────────────────────
async def fetch_openai():
    url = "https://platform.openai.com/docs/models"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as c:
            r = await c.get(url, headers=HEADERS)
            r.raise_for_status()

        text = r.text
        seen, models = set(), []

        # Patterns for known OpenAI model families
        patterns = [
            r"gpt-4o(?:-mini)?-\d{4}-\d{2}-\d{2}",
            r"o[1-9](?:-mini|-preview|-\d{4}-\d{2}-\d{2})?",
            r"gpt-4-turbo(?:-\d{4}-\d{2}-\d{2})?",
        ]
        for pat in patterns:
            for match in re.findall(pat, text):
                if match not in seen:
                    seen.add(match)
                    models.append({"id": match, "name": match})

        if models:
            return models[:8]
    except Exception:
        pass
    return _fallback_openai()


def _fallback_openai():
    return [
        {"id": "gpt-4o-2024-11-20",       "name": "GPT-4o (Nov 2024)"},
        {"id": "gpt-4o-mini-2024-07-18",   "name": "GPT-4o mini"},
        {"id": "o1-2024-12-17",            "name": "o1"},
        {"id": "o3-mini-2025-01-31",       "name": "o3-mini"},
        {"id": "o3-2025-04-16",            "name": "o3"},
        {"id": "o4-mini-2025-04-16",       "name": "o4-mini"},
    ]


# ── Google ─────────────────────────────────────────────────────────────────────
async def fetch_google():
    url = "https://ai.google.dev/gemini-api/docs/models"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as c:
            r = await c.get(url, headers=HEADERS)
            r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        seen, models = set(), []

        for table in soup.find_all("table"):
            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if cells:
                    code = cells[0].find("code")
                    text = code.get_text(strip=True) if code else cells[0].get_text(strip=True)
                    if "gemini" in text.lower() and text not in seen:
                        seen.add(text)
                        models.append({"id": text, "name": text})

        if not models:
            # Fallback: regex on raw HTML, filter to real model IDs
            raw_matches = re.findall(r"gemini-[\d]+\.[\d]+[\w.-]*", r.text, re.IGNORECASE)
            for match in raw_matches:
                m = match.rstrip(".,/\"'")
                # Skip file extensions and non-model strings
                if re.search(r"\.(png|svg|jpg|gif|js|css|json)$", m, re.IGNORECASE):
                    continue
                if m.lower() not in seen and len(m) > 7:
                    seen.add(m.lower())
                    models.append({"id": m, "name": m})

        return models[:8] if models else _fallback_google()
    except Exception:
        return _fallback_google()


def _fallback_google():
    return [
        {"id": "gemini-2.5-pro",          "name": "Gemini 2.5 Pro"},
        {"id": "gemini-2.0-flash",        "name": "Gemini 2.0 Flash"},
        {"id": "gemini-2.0-flash-lite",   "name": "Gemini 2.0 Flash Lite"},
        {"id": "gemini-1.5-pro-002",      "name": "Gemini 1.5 Pro"},
        {"id": "gemini-1.5-flash-002",    "name": "Gemini 1.5 Flash"},
    ]


# ── Meta ───────────────────────────────────────────────────────────────────────
async def fetch_meta():
    """Uses Hugging Face public API — no auth needed."""
    url = (
        "https://huggingface.co/api/models"
        "?author=meta-llama&sort=lastModified&direction=-1&limit=30"
    )
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as c:
            r = await c.get(url, headers={"User-Agent": HEADERS["User-Agent"]})
            r.raise_for_status()
        data = r.json()

        seen_families, models = set(), []
        skip_terms = ["gguf", "awq", "gptq", "hf-", "-hf", "guard", "prompt-guard"]

        for item in data:
            full_id = item.get("modelId", "")
            name = full_id.split("/")[-1] if "/" in full_id else full_id
            # Must be a Llama model
            if not name or "llama" not in name.lower():
                continue
            if any(t in name.lower() for t in skip_terms):
                continue
            family = re.sub(r"-\d+[bBmMtT].*$", "", name, flags=re.IGNORECASE)
            if family not in seen_families:
                seen_families.add(family)
                updated = (item.get("lastModified") or "")[:10]
                models.append({"id": name, "name": name, "updated": updated})

        # Sort by major.minor version descending (e.g. Llama-4 > Llama-3.3 > Llama-3.1)
        def llama_sort(m):
            match = re.search(r"llama-(\d+)(?:[.-](\d+))?", m["id"], re.IGNORECASE)
            if match:
                return (int(match.group(1)), int(match.group(2) or 0))
            return (0, 0)

        models.sort(key=llama_sort, reverse=True)
        return models[:6] if models else _fallback_meta()
    except Exception:
        return _fallback_meta()


def _fallback_meta():
    return [
        {"id": "Llama-3.3-70B-Instruct",          "name": "Llama 3.3 70B Instruct"},
        {"id": "Llama-3.2-90B-Vision-Instruct",    "name": "Llama 3.2 90B Vision"},
        {"id": "Llama-3.1-405B-Instruct",          "name": "Llama 3.1 405B Instruct"},
        {"id": "Llama-3.2-11B-Vision-Instruct",    "name": "Llama 3.2 11B Vision"},
        {"id": "Llama-Guard-3-8B",                 "name": "Llama Guard 3 8B"},
    ]


# ── NVIDIA ─────────────────────────────────────────────────────────────────────
async def fetch_nvidia():
    """Try NVIDIA's public NIM catalog API — filter to nvidia/* models only."""
    url = "https://integrate.api.nvidia.com/v1/models"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as c:
            r = await c.get(url, headers={"User-Agent": HEADERS["User-Agent"]})
            if r.status_code == 200:
                data = r.json()
                models = []
                for item in data.get("data", []):
                    mid = item.get("id", "")
                    # Only include NVIDIA's own models
                    if mid and mid.startswith("nvidia/"):
                        label = mid.split("/")[-1]
                        models.append({"id": mid, "name": label})
                if models:
                    # Prioritise Nemotron / Cosmos-Nemotron flagship models
                    priority = [m for m in models if "nemotron" in m["name"] or "cosmos" in m["name"]]
                    rest     = [m for m in models if m not in priority]
                    return (priority + rest)[:8]
    except Exception:
        pass
    return _fallback_nvidia()


def _fallback_nvidia():
    return [
        {"id": "nvidia/llama-3.1-nemotron-70b-instruct",   "name": "Nemotron 70B Instruct"},
        {"id": "nvidia/llama-3.3-nemotron-super-49b-v1",   "name": "Nemotron Super 49B"},
        {"id": "nvidia/llama-3.1-nemotron-nano-8b-v1",     "name": "Nemotron Nano 8B"},
        {"id": "nvidia/mistral-nemo-minitron-8b-8k-instruct", "name": "Minitron 8B Instruct"},
        {"id": "nvidia/nv-embedqa-e5-v5",                  "name": "NV-EmbedQA E5"},
    ]


# ── Mistral ────────────────────────────────────────────────────────────────────
async def fetch_mistral():
    url = "https://docs.mistral.ai/getting-started/models/overview/"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as c:
            r = await c.get(url, headers=HEADERS)
            r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        seen, models = set(), []

        for table in soup.find_all("table"):
            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if cells:
                    code = cells[0].find("code")
                    text = code.get_text(strip=True) if code else cells[0].get_text(strip=True)
                    if text and len(text) > 3 and text not in seen:
                        seen.add(text)
                        models.append({"id": text, "name": text})

        if not models:
            page_text = soup.get_text()
            pats = [r"mistral-[\w.-]+", r"codestral-[\w.-]+",
                    r"pixtral-[\w.-]+", r"mixtral-[\w.-]+"]
            for pat in pats:
                for match in re.findall(pat, page_text, re.IGNORECASE):
                    m = match.rstrip(".,)")
                    if m.lower() not in seen:
                        seen.add(m.lower())
                        models.append({"id": m, "name": m})

        return models[:8] if models else _fallback_mistral()
    except Exception:
        return _fallback_mistral()


def _fallback_mistral():
    return [
        {"id": "mistral-large-2411",          "name": "Mistral Large (Nov 2024)"},
        {"id": "mistral-small-2501",           "name": "Mistral Small (Jan 2025)"},
        {"id": "codestral-2501",              "name": "Codestral (Jan 2025)"},
        {"id": "pixtral-large-2411",          "name": "Pixtral Large (Nov 2024)"},
        {"id": "mixtral-8x22b-instruct-v0.1", "name": "Mixtral 8x22B Instruct"},
        {"id": "mistral-embed",               "name": "Mistral Embed"},
    ]


# ── Aggregate ──────────────────────────────────────────────────────────────────
PROVIDERS = [
    ("anthropic", "Anthropic", fetch_anthropic),
    ("openai",    "OpenAI",    fetch_openai),
    ("google",    "Google",    fetch_google),
    ("meta",      "Meta",      fetch_meta),
    ("nvidia",    "NVIDIA",    fetch_nvidia),
    ("mistral",   "Mistral",   fetch_mistral),
]


async def fetch_all():
    tasks = [fn() for _, _, fn in PROVIDERS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    out = {}
    for (key, name, _), result in zip(PROVIDERS, results):
        if isinstance(result, Exception):
            out[key] = {"name": name, "models": [], "error": str(result)}
        else:
            out[key] = {"name": name, "models": result or [], "error": None}
    return out
