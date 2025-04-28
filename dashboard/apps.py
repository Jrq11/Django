from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'  # Make sure this is correct and reflects your app's name

    def ready(self):
        import dashboard.signals  
        
