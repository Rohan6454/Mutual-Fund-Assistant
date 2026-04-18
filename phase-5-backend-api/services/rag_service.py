from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from types import ModuleType

logger = logging.getLogger(__name__)

_phase4_module: ModuleType | None = None
_models_loaded = False


def _preload_models():
    """Preload embedding models to prevent timeout issues."""
    global _models_loaded
    if _models_loaded:
        return
    
    try:
        # Import and preload the embedding model
        repo_root = Path(__file__).resolve().parents[2]
        phase2_path = repo_root / "phase-2-document-processing"
        phase3_path = repo_root / "phase-3-retrieval-engine"
        
        # Add paths if not already there
        import sys
        if str(phase2_path) not in sys.path:
            sys.path.insert(0, str(phase2_path))
        if str(phase3_path) not in sys.path:
            sys.path.insert(0, str(phase3_path))
        
        # Import embeddings module to trigger model loading
        embeddings_path = phase2_path / "embeddings.py"
        spec = importlib.util.spec_from_file_location("embeddings", embeddings_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load embeddings from {embeddings_path}")
        embeddings_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(embeddings_module)
        
        # Trigger model loading by creating a dummy embedding
        _ = embeddings_module.embed_query("test")
        
        _models_loaded = True
        logger.info("Models preloaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to preload models: {e}")
        # Don't raise exception - allow system to work without preloading


def _load_phase4_rag_engine() -> ModuleType:
    global _phase4_module
    if _phase4_module is not None:
        return _phase4_module
    
    # Ensure models are loaded before RAG engine
    _preload_models()
    
    repo_root = Path(__file__).resolve().parents[2]
    rag_path = repo_root / "phase-4-response-generation" / "rag_engine.py"
    spec = importlib.util.spec_from_file_location("phase4_rag_engine_runtime", rag_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Phase 4 rag engine from {rag_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _phase4_module = module
    return module


def answer_query(message: str) -> dict:
    rag = _load_phase4_rag_engine()
    return rag.answer_query(message)
