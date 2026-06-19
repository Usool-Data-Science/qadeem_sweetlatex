"""
recommendations/management/commands/run_evaluation.py

Thesis evaluation command. Runs the full offline evaluation suite and
prints a formatted results table suitable for copy-paste into the thesis.

Usage:
    python manage.py run_evaluation
    python manage.py run_evaluation --ragas-only
    python manage.py run_evaluation --recsys-only
    python manage.py run_evaluation --sessions <uuid1> <uuid2>
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run the full thesis evaluation suite (RAGAS + RecSys metrics)."

    def add_arguments(self, parser):
        parser.add_argument("--ragas-only",   action="store_true")
        parser.add_argument("--recsys-only",  action="store_true")
        parser.add_argument("--sessions",     nargs="+", help="Specific session UUIDs for RAGAS")

    def handle(self, *args, **options):
        self.stdout.write("\n" + "═" * 60)
        self.stdout.write("  SweetLatex Thesis Evaluation Suite")
        self.stdout.write("═" * 60 + "\n")

        if not options["ragas_only"]:
            self._run_recsys_evaluation()

        if not options["recsys_only"]:
            self._run_ragas_evaluation(options.get("sessions"))

        self.stdout.write("\n" + self.style.SUCCESS("Evaluation complete."))

    def _run_recsys_evaluation(self):
        """Print metrics from the MLModelRegistry for all active models."""
        self.stdout.write("\n── Recommendation System Metrics ──────────────────────\n")

        from recommendations.models import MLModelRegistry

        active_models = MLModelRegistry.objects.filter(is_active=True).order_by("model_type")
        if not active_models.exists():
            self.stdout.write(self.style.WARNING(
                "No active model checkpoints found. Train models first:\n"
                "  python manage.py shell -c \"from recommendations.tasks import train_bpr; train_bpr()\""
            ))
            return

        # Header
        self.stdout.write(f"{'Model':<12} {'Version':<20} {'P@5':<8} {'R@5':<8} "
                          f"{'NDCG@10':<10} {'P@10':<8} {'Rows':<8} {'Time(s)'}")
        self.stdout.write("─" * 80)

        for m in active_models:
            metrics = m.metrics
            self.stdout.write(
                f"{m.model_type:<12} "
                f"{m.version:<20} "
                f"{metrics.get('precision@5', 'N/A'):<8} "
                f"{metrics.get('recall@5', 'N/A'):<8} "
                f"{metrics.get('ndcg@10', 'N/A'):<10} "
                f"{metrics.get('precision@10', 'N/A'):<8} "
                f"{m.trained_on_rows:<8} "
                f"{m.training_duration_seconds}"
            )

    def _run_ragas_evaluation(self, session_ids=None):
        """Trigger RAGAS evaluation and print aggregated results."""
        self.stdout.write("\n── RAG Chatbot Evaluation (RAGAS) ─────────────────────\n")

        from chatbot.models import ChatMessage

        unevaluated = ChatMessage.objects.filter(
            role="assistant",
            faithfulness__isnull=True,
        ).exclude(retrieved_chunks=[]).count()

        if unevaluated == 0:
            self.stdout.write(self.style.WARNING(
                "No unevaluated assistant messages found.\n"
                "Chat with the bot first to generate evaluation data."
            ))
        else:
            self.stdout.write(f"Found {unevaluated} unevaluated messages — running RAGAS...")
            from chatbot.tasks import run_ragas_evaluation
            result = run_ragas_evaluation(session_ids=session_ids)

            if "error" in result:
                self.stdout.write(self.style.ERROR(f"RAGAS failed: {result['error']}"))
                return

            self.stdout.write(f"\n{'Metric':<25} {'Score'}")
            self.stdout.write("─" * 40)
            self.stdout.write(f"{'Faithfulness':<25} {result.get('faithfulness', 'N/A')}")
            self.stdout.write(f"{'Answer Relevance':<25} {result.get('answer_relevance', 'N/A')}")
            self.stdout.write(f"{'Context Precision':<25} {result.get('context_precision', 'N/A')}")
            self.stdout.write(f"\nMessages evaluated: {result.get('evaluated', 0)}")

        # Always print historical averages from DB
        from django.db.models import Avg
        averages = ChatMessage.objects.filter(
            role="assistant",
            faithfulness__isnull=False,
        ).aggregate(
            avg_faithfulness=Avg("faithfulness"),
            avg_answer_relevance=Avg("answer_relevance"),
            avg_context_precision=Avg("context_precision"),
        )

        total = ChatMessage.objects.filter(
            role="assistant", faithfulness__isnull=False
        ).count()

        if total > 0:
            self.stdout.write(f"\n── Historical averages across {total} evaluated messages ──")
            self.stdout.write(f"{'Faithfulness':<25} {averages['avg_faithfulness']:.4f}")
            self.stdout.write(f"{'Answer Relevance':<25} {averages['avg_answer_relevance']:.4f}")
            self.stdout.write(f"{'Context Precision':<25} {averages['avg_context_precision']:.4f}")