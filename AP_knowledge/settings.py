import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-test-key-replace-this-in-production'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'modeltranslation', # 必须在 admin 之前
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'captcha',
    'taggit',
    'martor',     # 编辑器
    'imagekit',   # 图片处理
    'mptt',       # 多级分类
    'knowledge',
    'feedback',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', # 即使做纯中文，这个也建议留着，防报错
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'AP_knowledge.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'AP_knowledge.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# === 国际化配置 (全中文) ===
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# modeltranslation 默认设置
MODELTRANSLATION_DEFAULT_LANGUAGE = 'zh-hans'
LANGUAGES = (
    ('zh-hans', '简体中文'),
    # 暂时隐藏其他语言，集中精力做好中文
    # ('en', 'English'),
)

# === 静态文件与媒体文件 ===
STATIC_URL = '/static/'
STATICFILES_DIRS = [ BASE_DIR / "static" ]

# 必须配置 Media，否则图片上传后无法显示
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# === Martor 编辑器配置 (修复上传问题) ===
# 这里的路径必须是相对于 MEDIA_ROOT 的
MARTOR_UPLOAD_PATH = 'images/uploads'
MARTOR_UPLOAD_URL = '/media/images/uploads/' # 前端访问路径
MARTOR_ENABLE_CONFIGS = {
    'emoji': 'true',
    'imgur': 'false', # 关闭 imgur，使用本地上传
    'mention': 'false',
    'jquery': 'true', # 必须开启，否则上传插件不工作
    'living': 'false',
    'spellcheck': 'false',
    'hljs': 'true',
}
# 让工具栏显示标签，方便识别
MARTOR_ENABLE_LABEL = True

# 默认主键
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
X_FRAME_OPTIONS = 'SAMEORIGIN'