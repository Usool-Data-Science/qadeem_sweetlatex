"""
ml/bpr.py

Bayesian Personalised Ranking (BPR) collaborative filtering.

Implementation uses the `cornac` library which provides:
  - BPR-MF with configurable latent factors
  - Built-in train/test split and evaluation (Precision@K, Recall@K, NDCG@K)
  - Serialisable model for Celery-based nightly retraining

Reference: Rendle et al. "BPR: Bayesian Personalized Ranking from Implicit
Feedback", UAI 2009.

Usage:
  trainer = BPRTrainer()
  metrics = trainer.train()            # called by Celery task
  scores  = trainer.score_for_user(user_id, candidate_product_ids)
"""

import logging
import pickle
from pathlib import Path
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

BPR_MODEL_PATH = Path(getattr(settings, "BPR_MODEL_PATH", "/app/ml_models/bpr.pkl"))
BPR_MAPPINGS_PATH = Path(
    getattr(settings, "BPR_MODEL_PATH", "/app/ml_models/bpr_mappings.pkl")
)


class BPRTrainer:
    """
    Trains BPR-MF on implicit interaction data from the interactions app.

    Interaction weights:
        view=1, click=1.5, wishlist=2, cart_add=3, purchase=5
    These are already stored on UserInteraction.weight so we read them directly.
    """

    def __init__(
        self,
        k: int = 64,
        learning_rate: float = 0.01,
        lambda_reg: float = 0.001,
        n_epochs: int = 50,
    ):
        self.k = k
        self.learning_rate = learning_rate
        self.lambda_reg = lambda_reg
        self.n_epochs = n_epochs
        self._model = None
        self._user_map: dict[int, str] = {}  # cornac_uid → django_user_pk
        self._item_map: dict[int, str] = {}  # cornac_iid → product_uuid
        self._user_map_inv: dict[str, int] = {}
        self._item_map_inv: dict[str, int] = {}

    def _load_interactions(self) -> tuple[list, list, list]:
        """
        Pull interaction data from DB and return (user_ids, item_ids, weights).
        We use Django PKs as integer IDs for cornac, then maintain a mapping.
        """
        from interactions.models import UserInteraction

        rows = (
            UserInteraction.objects.filter(user__isnull=False, product__isnull=False)
            .exclude(interaction_type="cart_remove")
            .values("user_id", "product_id", "weight")
        )

        # Build mappings
        all_users = sorted(set(str(r["user_id"]) for r in rows))
        all_items = sorted(set(str(r["product_id"]) for r in rows))

        self._user_map_inv = {uid: i for i, uid in enumerate(all_users)}
        self._item_map_inv = {iid: i for i, iid in enumerate(all_items)}
        self._user_map = {i: uid for uid, i in self._user_map_inv.items()}
        self._item_map = {i: iid for iid, i in self._item_map_inv.items()}

        users, items, weights = [], [], []
        seen = set()
        for r in rows:
            key = (str(r["user_id"]), str(r["product_id"]))
            if key in seen:
                continue
            seen.add(key)
            users.append(self._user_map_inv[str(r["user_id"])])
            items.append(self._item_map_inv[str(r["product_id"])])
            weights.append(float(r["weight"]))

        return users, items, weights

    def train(self) -> dict:
        """
        Train BPR-MF and persist the model checkpoint.
        Returns evaluation metrics for logging to MLModelRegistry.
        """
        try:
            import cornac
            from cornac.eval_methods import RatioSplit
            from cornac.metrics import NDCG, Precision, Recall
            from cornac.models import BPR
        except ImportError as e:
            raise ImportError(
                "cornac not installed. Add 'cornac' to requirements.txt"
            ) from e

        import time

        start = time.time()

        users, items, weights = self._load_interactions()
        if len(users) < 10:
            logger.warning(
                "Insufficient interaction data (%d rows) — skipping BPR training.",
                len(users),
            )
            return {"skipped": True, "reason": "insufficient_data", "rows": len(users)}

        logger.info(
            "Training BPR on %d interactions (%d users, %d items)",
            len(users),
            len(set(users)),
            len(set(items)),
        )

        data = cornac.data.Dataset.from_uir(zip(users, items, weights), seed=42)

        eval_method = RatioSplit(
            data=data,
            test_size=0.1,
            val_size=0.05,
            rating_threshold=1.0,
            seed=42,
            verbose=False,
        )

        model = BPR(
            k=self.k,
            learning_rate=self.learning_rate,
            lambda_reg=self.lambda_reg,
            n_epochs=self.n_epochs,
            seed=42,
            verbose=False,
        )

        exp = cornac.Experiment(
            eval_method=eval_method,
            models=[model],
            metrics=[
                Precision(k=5),
                Recall(k=5),
                NDCG(k=10),
                Precision(k=10),
            ],
            verbose=False,
        )
        exp.run()

        self._model = model
        duration = int(time.time() - start)

        # Extract metrics from cornac result
        result = exp.result[0]
        metrics = {
            "precision@5": round(result.metric_avg_results.get("Precision@5", 0), 4),
            "recall@5": round(result.metric_avg_results.get("Recall@5", 0), 4),
            "ndcg@10": round(result.metric_avg_results.get("NDCG@10", 0), 4),
            "precision@10": round(result.metric_avg_results.get("Precision@10", 0), 4),
            "n_users": len(set(users)),
            "n_items": len(set(items)),
            "n_interactions": len(users),
            "duration_seconds": duration,
        }

        # Persist
        BPR_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(BPR_MODEL_PATH, "wb") as f:
            pickle.dump(self._model, f)
        with open(BPR_MAPPINGS_PATH, "wb") as f:
            pickle.dump(
                {
                    "user_map": self._user_map,
                    "item_map": self._item_map,
                    "user_map_inv": self._user_map_inv,
                    "item_map_inv": self._item_map_inv,
                },
                f,
            )

        logger.info("BPR training complete: %s", metrics)
        return metrics

    @classmethod
    def load(cls) -> Optional["BPRTrainer"]:
        """Load a persisted BPR model from disk."""
        if not BPR_MODEL_PATH.exists() or not BPR_MAPPINGS_PATH.exists():
            logger.warning("No BPR checkpoint found at %s", BPR_MODEL_PATH)
            return None

        instance = cls()
        with open(BPR_MODEL_PATH, "rb") as f:
            instance._model = pickle.load(f)
        with open(BPR_MAPPINGS_PATH, "rb") as f:
            mappings = pickle.load(f)
        instance._user_map = mappings["user_map"]
        instance._item_map = mappings["item_map"]
        instance._user_map_inv = mappings["user_map_inv"]
        instance._item_map_inv = mappings["item_map_inv"]
        return instance

    def score_for_user(
        self,
        user_pk: str,
        candidate_product_ids: list[str],
    ) -> dict[str, float]:
        """
        Return BPR scores for a list of candidate products for a given user.

        Args:
            user_pk:               Django user PK as string
            candidate_product_ids: list of product UUID strings

        Returns:
            dict mapping product_uuid → BPR score (higher = more recommended)
        """
        if self._model is None:
            return {}

        uid = self._user_map_inv.get(str(user_pk))
        if uid is None:
            return {}  # unseen user — caller falls back to cold-start

        scores = {}
        for pid in candidate_product_ids:
            iid = self._item_map_inv.get(pid)
            if iid is None:
                continue
            try:
                score = float(self._model.score(uid, iid))
                scores[pid] = score
            except Exception:
                continue

        return scores
