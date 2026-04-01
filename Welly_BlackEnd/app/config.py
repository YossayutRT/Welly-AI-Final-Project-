from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency fallback
    def load_dotenv(*args, **kwargs):  # type: ignore[no-redef]
        return False


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


def _resolve_snapshot_path(model_name: str) -> Path | None:
    if "/" not in model_name:
        return None

    namespace, repo = model_name.split("/", 1)
    cache_root = Path.home() / ".cache" / "huggingface" / "hub"
    model_root = cache_root / f"models--{namespace}--{repo}"
    if not model_root.exists():
        return None

    ref_path = model_root / "refs" / "main"
    if ref_path.exists():
        revision = ref_path.read_text(encoding="utf-8").strip()
        snapshot = model_root / "snapshots" / revision
        if snapshot.exists():
            return snapshot

    snapshots_dir = model_root / "snapshots"
    if not snapshots_dir.exists():
        return None

    candidates = [path for path in snapshots_dir.iterdir() if path.is_dir()]
    if not candidates:
        return None

    return max(candidates, key=lambda path: path.stat().st_mtime)


def _resolve_model_path(model_name: str) -> Path | None:
    explicit_path = os.getenv("WELLY_MODEL_PATH")
    if explicit_path:
        path = Path(explicit_path).expanduser().resolve()
        if path.exists():
            return path

    if Path(model_name).expanduser().exists():
        return Path(model_name).expanduser().resolve()

    return _resolve_snapshot_path(model_name)


@dataclass(frozen=True)
class Settings:
    project_root: Path
    notebooks_dir: Path
    data_dir: Path
    outputs_dir: Path
    knowledge_dir: Path
    model_name: str
    model_path: Path | None
    model_tag: str
    llm_model: str
    groq_api_key: str | None
    embeddings_local_only: bool
    default_top_k: int
    allowed_origins: list[str]

    @property
    def knowledge_index_dir(self) -> Path:
        return self.notebooks_dir / f"faiss_welly_index_{self.model_tag}"

    @property
    def recipes_index_dir(self) -> Path:
        return self.notebooks_dir / f"faiss_recipes_index_{self.model_tag}"

    @property
    def calories_index_dir(self) -> Path:
        return self.notebooks_dir / f"faiss_calories_index_{self.model_tag}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env", override=False)
    load_dotenv(project_root / "Welly_BlackEnd" / ".env", override=False)

    model_name = os.getenv("WELLY_MODEL_NAME", "intfloat/multilingual-e5-small")
    model_path = _resolve_model_path(model_name)
    model_tag = model_name.split("/")[-1].replace("-", "_")
    llm_model = os.getenv("WELLY_LLM_MODEL", "llama-3.1-8b-instant")

    return Settings(
        project_root=project_root,
        notebooks_dir=project_root / "Notebooks",
        data_dir=project_root / "data",
        outputs_dir=project_root / "outputs",
        knowledge_dir=project_root / "data" / "knowledge",
        model_name=model_name,
        model_path=model_path,
        model_tag=model_tag,
        llm_model=llm_model,
        groq_api_key=os.getenv("GROQ_API_KEY") or os.getenv("GROQ_TOKEN"),
        embeddings_local_only=_env_bool("WELLY_EMBEDDINGS_LOCAL_ONLY", True),
        default_top_k=int(os.getenv("WELLY_TOP_K", "4")),
        allowed_origins=_env_list(
            "WELLY_ALLOWED_ORIGINS",
            [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ],
        ),
    )
