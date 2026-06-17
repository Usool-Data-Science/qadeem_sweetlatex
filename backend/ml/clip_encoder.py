"""
ml/clip_encoder.py

Singleton CLIP encoder — loads the model once per worker process and reuses it.
Supports both image-URL-based encoding (for products) and text encoding (for
visual search queries like "red summer dress").

Model: ViT-B/32 (configurable via settings.CLIP_MODEL_NAME)
Output dim: 512
"""

import logging
from io import BytesIO
from typing import Optional

import numpy as np
import requests
import torch
from django.conf import settings
from PIL import Image

logger = logging.getLogger(__name__)

_clip_model = None
_clip_preprocess = None
_clip_device = None


def _load_clip():
    """Lazy-load CLIP — only imports on first call, cached in module globals."""
    global _clip_model, _clip_preprocess, _clip_device

    if _clip_model is not None:
        return _clip_model, _clip_preprocess, _clip_device

    try:
        import clip  # openai-clip
    except ImportError as e:
        raise ImportError(
            "openai-clip not installed. Add 'openai-clip' to requirements.txt"
        ) from e

    model_name = getattr(settings, "CLIP_MODEL_NAME", "ViT-B/32")
    _clip_device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Loading CLIP model %s on %s", model_name, _clip_device)

    _clip_model, _clip_preprocess = clip.load(model_name, device=_clip_device)
    _clip_model.eval()

    logger.info("CLIP model loaded successfully (dim=512)")
    return _clip_model, _clip_preprocess, _clip_device


def encode_image_from_url(image_url: str) -> Optional[list[float]]:
    """
    Download image from URL and return a 512-d normalised CLIP embedding.
    Returns None on any error so the caller can decide how to handle failure.
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")
        return encode_pil_image(image)
    except Exception as exc:
        logger.error("Failed to encode image from URL %s: %s", image_url, exc)
        return None


def encode_pil_image(image: Image.Image) -> Optional[list[float]]:
    """Encode a PIL Image object — used by the visual search endpoint."""
    try:
        model, preprocess, device = _load_clip()
        tensor = preprocess(image).unsqueeze(0).to(device)
        with torch.no_grad():
            features = model.encode_image(tensor)
            features = features / features.norm(dim=-1, keepdim=True)  # L2 normalise
        return features.cpu().numpy().flatten().tolist()
    except Exception as exc:
        logger.error("PIL image encoding failed: %s", exc)
        return None


def encode_text(text: str) -> Optional[list[float]]:
    """
    Encode a text query into the CLIP embedding space.
    Enables cross-modal search: text query → similar product images.
    """
    try:
        import clip

        model, _, device = _load_clip()
        tokens = clip.tokenize([text[:77]]).to(device)  # CLIP max 77 tokens
        with torch.no_grad():
            features = model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
        return features.cpu().numpy().flatten().tolist()
    except Exception as exc:
        logger.error("Text encoding failed for '%s': %s", text, exc)
        return None


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0
