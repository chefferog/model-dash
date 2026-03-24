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

# ── Model quality filters ──────────────────────────────────────────────────────
# Patterns that indicate the model is NOT a text-generation LLM
_NON_LLM = re.compile(
    r"\bembed"               # embedding/retrieval models (prefix match covers embedqa, embeddings, etc.)
    r"|\btts\b|-tts\b"       # text-to-speech
    r"|native-audio"          # audio-only models
    r"|-image\b|image-preview"# image-generation models (e.g. gemini-2.5-flash-image)
    r"|computer-use"          # specialized tool-use variants (not general-purpose LLMs)
    r"|\breward\b"            # reward / preference models
    r"|safety-guard|nemoguard"# content safety classifiers
    r"|\bpii\b|gliner"        # PII / NER classifiers
    r"|diffusion"             # diffusion image models
    r"|whisper|speech-to-text"# ASR models
    r"|\bclip\b"              # vision-only encoders
    r"|\bretriev"             # retriever / reranker models
    r"|\btranslat"            # translation-only models
    r"|streampetr|\bvila\b"   # non-LLM vision/tracking models
    ,
    re.IGNORECASE,
)

# Patterns that indicate a model is legacy or archived
_LEGACY = re.compile(
    r"\blegacy\b|\barchived\b|\bdeprecated\b"
    r"|davinci|babbage|curie|text-ada"  # OpenAI legacy completions
    r"|gpt-3\.5"                        # OpenAI older generation
    ,
    re.IGNORECASE,
)


def is_llm(model_id: str) -> bool:
    """Return True if the model ID looks like a text-generation LLM."""
    return not _NON_LLM.search(model_id)


def is_current(model_id: str) -> bool:
    """Return True if the model is not marked legacy/archived/deprecated."""
    return not _LEGACY.search(model_id)


def keep(model_id: str) -> bool:
    return is_llm(model_id) and is_current(model_id)


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
            # Normalize: strip trailing -v\d+ alias so we don't show duplicates
            base = re.sub(r"-v\d+$", "", mid)
            if base not in seen_bases and len(base) > 8:
                seen_bases.add(base)
                models.append({"id": base, "name": base})

        models = [m for m in models if keep(m["id"])]

        # Keep only the latest version per model family (opus, sonnet, haiku, …)
        # Version key: (major, minor, date) — all extracted from the model ID
        def version_key(model_id):
            family_m = re.search(r"claude-(opus|sonnet|haiku|instant)", model_id, re.IGNORECASE)
            after = model_id[family_m.end():] if family_m else model_id
            date_m = re.search(r"(\d{8})", after)
            date = int(date_m.group(1)) if date_m else 0
            ver_nums = [int(n) for n in re.findall(r"\d+", after) if len(n) < 8]
            major = ver_nums[0] if len(ver_nums) > 0 else 0
            minor = ver_nums[1] if len(ver_nums) > 1 else 0
            return (major, minor, date)

        def family_name(model_id):
            m = re.search(r"claude-(opus|sonnet|haiku|instant)", model_id, re.IGNORECASE)
            return m.group(1).lower() if m else model_id

        best = {}  # family → model with highest version key
        for m in models:
            fam = family_name(m["id"])
            if fam not in best or version_key(m["id"]) > version_key(best[fam]["id"]):
                best[fam] = m

        result = sorted(best.values(), key=lambda m: version_key(m["id"]), reverse=True)
        return result if result else _fallback_anthropic()
    except Exception:
        return _fallback_anthropic()


def _fallback_anthropic():
    return [
        {"id": "claude-opus-4-6",              "name": "Claude Opus 4.6"},
        {"id": "claude-sonnet-4-6",             "name": "Claude Sonnet 4.6"},
        {"id": "claude-haiku-4-5-20251001",     "name": "Claude Haiku 4.5"},
        #{"id": "claude-3-5-sonnet-20241022",    "name": "Claude 3.5 Sonnet"},
        #{"id": "claude-3-5-haiku-20241022",     "name": "Claude 3.5 Haiku"},
        #{"id": "claude-3-opus-20240229",        "name": "Claude 3 Opus"},
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

        models = [m for m in models if keep(m["id"])]
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

        models = [m for m in models if keep(m["id"])]
        models = _latest_per_family_google(models)
        return models if models else _fallback_google()
    except Exception:
        return _fallback_google()


def _gemini_family_key(model_id):
    """Return (family_name, (major, minor), is_preview) for a Gemini model ID."""
    m = re.match(r"gemini-(\d+)\.(\d+)-(.*)", model_id, re.IGNORECASE)
    if not m:
        return None, (0, 0), True
    major, minor, rest = int(m.group(1)), int(m.group(2)), m.group(3)
    # Strip date-stamped preview suffix, then bare -preview
    family = re.sub(r"-preview-\d{2}-\d{4}$", "", rest)
    family = re.sub(r"-preview$", "", family)
    is_preview = "preview" in rest
    return family, (major, minor), is_preview


def _latest_per_family_google(models):
    """Keep one model per Gemini family (flash, flash-lite, pro, …), highest version wins.
    At equal version, prefer non-preview over preview."""
    best = {}  # family → (rank_tuple, model)
    for m in models:
        family, version, is_preview = _gemini_family_key(m["id"])
        if not family:
            continue
        # Rank: (major, minor, 1 if stable else 0) — higher is better
        rank = (version[0], version[1], 0 if is_preview else 1)
        if family not in best or rank > best[family][0]:
            best[family] = (rank, m)
    result = [v[1] for v in best.values()]
    result.sort(key=lambda m: _gemini_family_key(m["id"])[1], reverse=True)
    return result


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

        models = [m for m in models if keep(m["id"])]
        models = _latest_per_family_meta(models)
        return models if models else _fallback_meta()
    except Exception:
        return _fallback_meta()


def _meta_family_key(model_id):
    """Return (family_name, (major, minor)) for a Meta Llama model ID.
    Llama 4 variants (Maverick, Scout) are separate families.
    Llama 3.x text and vision are separate families; only the latest minor is kept per type."""
    major_m = re.search(r"llama-(\d+)", model_id, re.IGNORECASE)
    major = int(major_m.group(1)) if major_m else 0
    if major == 4:
        series_m = re.search(r"llama-4-(\w+?)-", model_id, re.IGNORECASE)
        series = series_m.group(1).lower() if series_m else "base"
        return f"llama4-{series}", (4, 0)
    elif major == 3:
        minor_m = re.search(r"llama-3\.(\d+)", model_id, re.IGNORECASE)  # dot-separated minor only
        minor = int(minor_m.group(1)) if minor_m else 0
        cap = "vision" if "vision" in model_id.lower() else "text"
        return f"llama3-{cap}", (3, minor)
    return model_id, (0, 0)


def _latest_per_family_meta(models):
    """Keep the latest Llama model per capability family."""
    best = {}
    for m in models:
        family, version = _meta_family_key(m["id"])
        if family not in best or version > best[family][0]:
            best[family] = (version, m)
    result = [v[1] for v in best.values()]
    result.sort(key=lambda m: _meta_family_key(m["id"])[1], reverse=True)
    return result


def _fallback_meta():
    return [
        {"id": "Llama-4-Maverick-17B-128E-Instruct", "name": "Llama 4 Maverick"},
        {"id": "Llama-4-Scout-17B-16E-Instruct",     "name": "Llama 4 Scout"},
        {"id": "Llama-3.3-70B-Instruct",             "name": "Llama 3.3 70B Instruct"},
        {"id": "Llama-3.2-90B-Vision-Instruct",      "name": "Llama 3.2 90B Vision"},
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
                    # Restrict to NVIDIA's flagship LLM families: Nemotron and Cosmos Reason
                    models = [m for m in models
                              if keep(m["id"]) and
                              ("nemotron" in m["name"] or "cosmos-reason" in m["name"])]
                    models = _latest_per_family_nvidia(models)
                    return models
    except Exception:
        pass
    return _fallback_nvidia()


def _nvidia_tier(model_id):
    """Return a tier label used to group Nemotron/Cosmos models into families."""
    name = model_id.split("/")[-1]
    if "cosmos-reason"    in name:   return "cosmos-reason"
    if "nemotron-nano-vl" in name:   return "nemotron-nano-vl"
    if "nemotron-nano"    in name:   return "nemotron-nano"
    if "nemotron-super"   in name:   return "nemotron-super"
    if "nemotron-ultra"   in name:   return "nemotron-ultra"
    if "nemotron"         in name:   return "nemotron-instruct"
    return name


def _nvidia_rank(model_id):
    """Rank key: (llama_major, llama_minor, ver_major, ver_minor, param_billions).
    Llama-based models (newer architecture) beat older standalone Nemotron models.
    Within the same base, higher version and larger params win."""
    llama_m  = re.search(r"llama-(\d+)\.(\d+)", model_id, re.IGNORECASE)
    llama_v  = (int(llama_m.group(1)), int(llama_m.group(2))) if llama_m else (0, 0)
    ver_m    = re.search(r"-v(\d+)(?:\.(\d+))?(?:\b|$)", model_id, re.IGNORECASE)
    ver      = (int(ver_m.group(1)), int(ver_m.group(2) or 0)) if ver_m else (0, 0)
    param_m  = re.search(r"-(\d+)b\b", model_id, re.IGNORECASE)
    params   = int(param_m.group(1)) if param_m else 0
    return llama_v + ver + (params,)


def _latest_per_family_nvidia(models):
    """Keep one model per Nemotron tier, preferring largest params then latest version."""
    best = {}
    for m in models:
        tier = _nvidia_tier(m["id"])
        rank = _nvidia_rank(m["id"])
        if tier not in best or rank > best[tier][0]:
            best[tier] = (rank, m)
    return [v[1] for v in best.values()]


def _fallback_nvidia():
    return [
        {"id": "nvidia/llama-3.1-nemotron-70b-instruct",      "name": "Nemotron 70B Instruct"},
        {"id": "nvidia/llama-3.3-nemotron-super-49b-v1.5",    "name": "Nemotron Super 49B"},
        {"id": "nvidia/llama-3.1-nemotron-ultra-253b-v1",     "name": "Nemotron Ultra 253B"},
        {"id": "nvidia/llama-3.1-nemotron-nano-8b-v1",        "name": "Nemotron Nano 8B"},
        {"id": "nvidia/llama-3.1-nemotron-nano-vl-8b-v1",     "name": "Nemotron Nano VL 8B"},
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

        models = [m for m in models if keep(m["id"])]
        return models[:8] if models else _fallback_mistral()
    except Exception:
        return _fallback_mistral()


def _fallback_mistral():
    return [
        {"id": "mistral-large-2411",          "name": "Mistral Large (Nov 2024)"},
        {"id": "mistral-small-2501",          "name": "Mistral Small (Jan 2025)"},
        {"id": "codestral-2501",              "name": "Codestral (Jan 2025)"},
        {"id": "pixtral-large-2411",          "name": "Pixtral Large (Nov 2024)"},
        {"id": "mixtral-8x22b-instruct-v0.1", "name": "Mixtral 8x22B Instruct"},
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
