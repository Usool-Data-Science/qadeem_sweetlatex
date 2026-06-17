"""
ml/sasrec.py

Self-Attentive Sequential Recommendation (SASRec) — PyTorch implementation.

Reference: Kang & McAuley, "Self-Attentive Sequential Recommendation",
ICDM 2018.  https://arxiv.org/abs/1808.09781

Architecture:
  - Item embedding layer
  - N stacked self-attention blocks (each: LayerNorm → MultiHeadAttn → FFN)
  - Causal (left-to-right) masking so the model only sees past items
  - Trained with binary cross-entropy on (positive item, sampled negatives)

Training data: UserInteraction sequences ordered by created_at,
filtered to PURCHASE + CART_ADD + WISHLIST events (high-quality signals).
"""

import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from django.conf import settings

logger = logging.getLogger(__name__)

SASREC_MODEL_PATH = Path(
    getattr(settings, "SASREC_MODEL_PATH", "/app/ml_models/sasrec.pt")
)
SASREC_META_PATH = SASREC_MODEL_PATH.parent / "sasrec_meta.pkl"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ── Model definition ──────────────────────────────────────────────────────────


class PointWiseFeedForward(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)


class SASRecBlock(nn.Module):
    def __init__(self, hidden_dim: int, n_heads: int, dropout: float):
        super().__init__()
        self.norm1 = nn.LayerNorm(hidden_dim, eps=1e-8)
        self.attn = nn.MultiheadAttention(
            hidden_dim, n_heads, dropout=dropout, batch_first=True
        )
        self.norm2 = nn.LayerNorm(hidden_dim, eps=1e-8)
        self.ffn = PointWiseFeedForward(hidden_dim, dropout)
        self.drop = nn.Dropout(dropout)

    def forward(self, x, attn_mask):
        # Self-attention with pre-norm
        residual = x
        x = self.norm1(x)
        x, _ = self.attn(x, x, x, attn_mask=attn_mask, need_weights=False)
        x = self.drop(x) + residual
        # FFN with pre-norm
        residual = x
        x = self.norm2(x)
        x = self.ffn(x) + residual
        return x


class SASRec(nn.Module):
    """
    Args:
        n_items:    total number of items (vocab size)
        maxlen:     maximum sequence length
        hidden_dim: embedding / attention dimension
        n_blocks:   number of transformer blocks
        n_heads:    attention heads
        dropout:    dropout probability
    """

    def __init__(
        self,
        n_items: int,
        maxlen: int = 50,
        hidden_dim: int = 128,
        n_blocks: int = 2,
        n_heads: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.n_items = n_items
        self.maxlen = maxlen
        self.hidden_dim = hidden_dim

        # +1 for padding token (index 0)
        self.item_emb = nn.Embedding(n_items + 1, hidden_dim, padding_idx=0)
        self.pos_emb = nn.Embedding(maxlen, hidden_dim)
        self.emb_drop = nn.Dropout(dropout)
        self.blocks = nn.ModuleList(
            [SASRecBlock(hidden_dim, n_heads, dropout) for _ in range(n_blocks)]
        )
        self.norm = nn.LayerNorm(hidden_dim, eps=1e-8)

        self._init_weights()

    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def _causal_mask(self, seq_len: int) -> torch.Tensor:
        """Upper-triangular mask — prevents attending to future positions."""
        mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool()
        return mask.to(DEVICE)

    def forward(self, seq: torch.Tensor) -> torch.Tensor:
        """
        Args:
            seq: (B, L) long tensor of item indices, padded with 0s on the left
        Returns:
            (B, L, D) sequence of hidden states
        """
        B, L = seq.shape
        positions = torch.arange(L, device=DEVICE).unsqueeze(0).expand(B, -1)

        x = self.item_emb(seq) + self.pos_emb(positions)
        x = self.emb_drop(x)

        mask = self._causal_mask(L)
        for block in self.blocks:
            x = block(x, mask)

        return self.norm(x)

    def predict(self, seq: torch.Tensor, item_indices: torch.Tensor) -> torch.Tensor:
        """
        Score candidate items for the last position in the sequence.
        Args:
            seq:          (1, L) input sequence
            item_indices: (K,)  candidate item indices to score
        Returns:
            (K,) logit scores
        """
        h = self.forward(seq)  # (1, L, D)
        last = h[:, -1, :]  # (1, D)
        item_embs = self.item_emb(item_indices)  # (K, D)
        return (last @ item_embs.T).squeeze(0)  # (K,)


# ── Trainer ───────────────────────────────────────────────────────────────────


class SASRecTrainer:
    def __init__(
        self,
        maxlen: int = 50,
        hidden_dim: int = 128,
        n_blocks: int = 2,
        n_heads: int = 2,
        dropout: float = 0.2,
        lr: float = 1e-3,
        n_epochs: int = 30,
        batch_size: int = 256,
    ):
        self.maxlen = maxlen
        self.hidden_dim = hidden_dim
        self.n_blocks = n_blocks
        self.n_heads = n_heads
        self.dropout = dropout
        self.lr = lr
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self._model: Optional[SASRec] = None
        self._item_map: dict[str, int] = {}  # product_uuid → int index
        self._item_map_inv: dict[int, str] = {}

    def _load_sequences(self) -> dict[str, list[str]]:
        """
        Load per-user item sequences ordered by time.
        Only high-signal events: PURCHASE, CART_ADD, WISHLIST.
        """
        from interactions.models import InteractionType, UserInteraction

        HIGH_SIGNAL = {
            InteractionType.PURCHASE,
            InteractionType.CART_ADD,
            InteractionType.WISHLIST,
        }

        rows = (
            UserInteraction.objects.filter(
                user__isnull=False,
                product__isnull=False,
                interaction_type__in=HIGH_SIGNAL,
            )
            .order_by("user_id", "created_at")
            .values("user_id", "product_id")
        )

        sequences: dict[str, list[str]] = {}
        for r in rows:
            uid = str(r["user_id"])
            pid = str(r["product_id"])
            sequences.setdefault(uid, []).append(pid)

        # Deduplicate consecutive repeats, keep order
        return {
            uid: list(dict.fromkeys(seq))
            for uid, seq in sequences.items()
            if len(seq) >= 3  # need at least 3 items to train
        }

    def _build_item_map(self, sequences: dict) -> None:
        all_items = sorted({item for seq in sequences.values() for item in seq})
        self._item_map = {pid: i + 1 for i, pid in enumerate(all_items)}  # 0 = padding
        self._item_map_inv = {i: pid for pid, i in self._item_map.items()}

    def _encode_sequence(self, seq: list[str]) -> list[int]:
        return [self._item_map[p] for p in seq if p in self._item_map]

    def train(self) -> dict:
        import time

        start = time.time()

        sequences = self._load_sequences()
        if len(sequences) < 5:
            logger.warning(
                "Only %d user sequences — skipping SASRec training.", len(sequences)
            )
            return {
                "skipped": True,
                "reason": "insufficient_sequences",
                "count": len(sequences),
            }

        self._build_item_map(sequences)
        n_items = len(self._item_map)
        logger.info(
            "SASRec training: %d users, %d unique items", len(sequences), n_items
        )

        self._model = SASRec(
            n_items=n_items,
            maxlen=self.maxlen,
            hidden_dim=self.hidden_dim,
            n_blocks=self.n_blocks,
            n_heads=self.n_heads,
            dropout=self.dropout,
        ).to(DEVICE)

        optimizer = torch.optim.Adam(self._model.parameters(), lr=self.lr)
        criterion = nn.BCEWithLogitsLoss()

        # Build training samples: (seq[-maxlen-1:-1], pos_item, neg_item)
        all_items_set = set(self._item_map.values())

        self._model.train()
        for epoch in range(self.n_epochs):
            epoch_loss = 0.0
            n_batches = 0

            # Simple sequential batching
            seqs_batch, pos_batch, neg_batch = [], [], []

            for uid, seq in sequences.items():
                encoded = self._encode_sequence(seq)
                for i in range(1, len(encoded)):
                    input_seq = encoded[:i][-self.maxlen :]
                    pos_item = encoded[i] if i < len(encoded) else encoded[-1]

                    # Pad left
                    pad_len = self.maxlen - len(input_seq)
                    padded = [0] * pad_len + input_seq

                    # Negative sampling
                    neg_item = pos_item
                    while neg_item in {pos_item}:
                        neg_item = np.random.randint(1, n_items + 1)

                    seqs_batch.append(padded)
                    pos_batch.append(pos_item)
                    neg_batch.append(neg_item)

                    if len(seqs_batch) >= self.batch_size:
                        loss = self._train_step(
                            optimizer, criterion, seqs_batch, pos_batch, neg_batch
                        )
                        epoch_loss += loss
                        n_batches += 1
                        seqs_batch, pos_batch, neg_batch = [], [], []

            if seqs_batch:
                loss = self._train_step(
                    optimizer, criterion, seqs_batch, pos_batch, neg_batch
                )
                epoch_loss += loss
                n_batches += 1

            if (epoch + 1) % 5 == 0:
                avg = epoch_loss / max(n_batches, 1)
                logger.debug(
                    "SASRec epoch %d/%d — loss=%.4f", epoch + 1, self.n_epochs, avg
                )

        # Persist
        SASREC_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self._model.state_dict(), SASREC_MODEL_PATH)
        with open(SASREC_META_PATH, "wb") as f:
            pickle.dump(
                {
                    "item_map": self._item_map,
                    "item_map_inv": self._item_map_inv,
                    "n_items": n_items,
                    "maxlen": self.maxlen,
                    "hidden_dim": self.hidden_dim,
                    "n_blocks": self.n_blocks,
                    "n_heads": self.n_heads,
                },
                f,
            )

        duration = int(time.time() - start)
        logger.info("SASRec training complete in %ds", duration)
        return {
            "n_users": len(sequences),
            "n_items": n_items,
            "epochs": self.n_epochs,
            "duration_seconds": duration,
        }

    def _train_step(self, optimizer, criterion, seqs, pos_items, neg_items) -> float:
        seqs_t = torch.tensor(seqs, dtype=torch.long, device=DEVICE)
        pos_t = torch.tensor(pos_items, dtype=torch.long, device=DEVICE)
        neg_t = torch.tensor(neg_items, dtype=torch.long, device=DEVICE)

        optimizer.zero_grad()
        h = self._model(seqs_t)[:, -1, :]  # last hidden state

        pos_emb = self._model.item_emb(pos_t)
        neg_emb = self._model.item_emb(neg_t)

        pos_logits = (h * pos_emb).sum(-1)
        neg_logits = (h * neg_emb).sum(-1)

        labels_pos = torch.ones_like(pos_logits)
        labels_neg = torch.zeros_like(neg_logits)

        loss = criterion(pos_logits, labels_pos) + criterion(neg_logits, labels_neg)
        loss.backward()
        nn.utils.clip_grad_norm_(self._model.parameters(), 1.0)
        optimizer.step()
        return loss.item()

    @classmethod
    def load(cls) -> Optional["SASRecTrainer"]:
        if not SASREC_MODEL_PATH.exists() or not SASREC_META_PATH.exists():
            logger.warning("No SASRec checkpoint at %s", SASREC_MODEL_PATH)
            return None

        with open(SASREC_META_PATH, "rb") as f:
            meta = pickle.load(f)

        instance = cls(
            maxlen=meta["maxlen"],
            hidden_dim=meta["hidden_dim"],
            n_blocks=meta["n_blocks"],
            n_heads=meta["n_heads"],
        )
        instance._item_map = meta["item_map"]
        instance._item_map_inv = meta["item_map_inv"]

        model = SASRec(
            n_items=meta["n_items"],
            maxlen=meta["maxlen"],
            hidden_dim=meta["hidden_dim"],
            n_blocks=meta["n_blocks"],
            n_heads=meta["n_heads"],
        ).to(DEVICE)
        model.load_state_dict(torch.load(SASREC_MODEL_PATH, map_location=DEVICE))
        model.eval()
        instance._model = model
        return instance

    def recommend(
        self,
        user_pk: str,
        top_k: int = 20,
        exclude_ids: Optional[set[str]] = None,
    ) -> list[tuple[str, float]]:
        """
        Given a user's purchase/cart history, predict the next best items.
        Returns list of (product_uuid, score) sorted best-first.
        """
        if self._model is None:
            return []

        from interactions.models import InteractionType, UserInteraction

        HIGH_SIGNAL = {
            InteractionType.PURCHASE,
            InteractionType.CART_ADD,
            InteractionType.WISHLIST,
        }

        seq_qs = (
            UserInteraction.objects.filter(
                user_id=user_pk, interaction_type__in=HIGH_SIGNAL, product__isnull=False
            )
            .order_by("created_at")
            .values_list("product_id", flat=True)
        )
        seq_pids = [str(p) for p in seq_qs]
        encoded = self._encode_sequence(seq_pids)[-self.maxlen :]

        if not encoded:
            return []

        pad_len = self.maxlen - len(encoded)
        padded = [0] * pad_len + encoded
        seq_t = torch.tensor([padded], dtype=torch.long, device=DEVICE)

        exclude_ids = exclude_ids or set()
        all_item_indices = torch.arange(1, self._model.n_items + 1, device=DEVICE)

        with torch.no_grad():
            scores = self._model.predict(seq_t, all_item_indices).cpu().numpy()

        results = []
        for idx, score in sorted(enumerate(scores), key=lambda x: -x[1]):
            pid = self._item_map_inv.get(idx + 1)
            if pid and pid not in exclude_ids:
                results.append((pid, float(score)))
            if len(results) >= top_k:
                break

        return results
