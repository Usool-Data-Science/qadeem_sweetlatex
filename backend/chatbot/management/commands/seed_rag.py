"""
chatbot/management/commands/seed_rag.py

Bootstrap command that queues RAG indexing for every product.
Run automatically from entrypoint.sh on container start.

Usage:
    python manage.py seed_rag             # always queue all products
    python manage.py seed_rag --if-empty  # only queue if Pinecone index is empty
    python manage.py seed_rag --force     # wipe Pinecone first, then requeue
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed the Pinecone RAG index by queuing all products for indexing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--if-empty",
            action="store_true",
            help="Only run if the Pinecone index has zero vectors.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete and recreate the Pinecone index before seeding.",
        )

    def handle(self, *args, **options):
        from core.models import Product

        # ── Check Pinecone index count if --if-empty ──────────────────────────
        if options["if_empty"]:
            try:
                from ml.rag_pipeline import _get_pinecone_index
                index = _get_pinecone_index()
                if index:
                    stats = index.describe_index_stats()
                    count = stats.get("total_vector_count", 0)
                    if count > 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Pinecone index already has {count} vectors — skipping seed."
                            )
                        )
                        return
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Could not check Pinecone index: {e} — proceeding.")
                )

        # ── Optional force wipe ───────────────────────────────────────────────
        if options["force"]:
            self.stdout.write("Force flag set — rebuilding Pinecone index from scratch...")
            from chatbot.tasks import rebuild_rag_index
            rebuild_rag_index.delay()
            self.stdout.write(self.style.SUCCESS("rebuild_rag_index task queued."))
            return

        # ── Queue indexing for every product ──────────────────────────────────
        from chatbot.tasks import index_product_chunks

        product_ids = list(Product.objects.values_list("product_id", flat=True))
        if not product_ids:
            self.stdout.write(self.style.WARNING("No products found — nothing to index."))
            return

        for pid in product_ids:
            index_product_chunks.delay(str(pid))

        self.stdout.write(
            self.style.SUCCESS(
                f"Queued RAG indexing for {len(product_ids)} products on the `ml` Celery queue."
            )
        )