# apps/ats/apps.py
from django.apps import AppConfig

class AtsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ats'  # Fixed: Full path