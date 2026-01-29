import os
from django.core.wsgi import get_wsgi_application

# 指向你的 settings 文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AP_knowledge.settings')

application = get_wsgi_application()