from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class SageSlugConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sage_slug'
    verbose_name = _("Django SAGE Slug")


    def ready(self):
        from sage_slug.settings import checks
