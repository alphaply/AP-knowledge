from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_superuser(sender, **kwargs):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        print("Creating default superuser: admin/123456")
        User.objects.create_superuser('admin', 'admin@example.com', '123456')

class KnowledgeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'knowledge'

    def ready(self):
        # 注册信号
        post_migrate.connect(create_default_superuser, sender=self)