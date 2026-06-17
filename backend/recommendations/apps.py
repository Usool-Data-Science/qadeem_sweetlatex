from django.apps import AppConfig


class RecommendationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recommendations"
    verbose_name = "Recommendation Engine"

    def ready(self):
        import recommendations.signals  # noqa: F401
