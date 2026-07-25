from django.apps import AppConfig


class CoursesConfig(AppConfig):
    name = 'courses'

    def ready(self):
        import courses.signals  # noqa: F401 — enregistre les signaux Django
