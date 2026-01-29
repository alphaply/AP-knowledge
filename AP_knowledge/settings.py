import os
from pathlib import Path

# 构建项目根目录路径
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥 (实习任务可以先写死，正式上线建议用环境变量)
SECRET_KEY = 'django-insecure-test-key-replace-this-in-production'

# 调试模式 (开发时开启，出错能看到详细信息)
DEBUG = True

# 允许访问的主机 (允许局域网访问，方便以后给同事看)
ALLOWED_HOSTS = ['*']

# 【重要】已安装的应用
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 第三方库
    'captcha',  # 验证码
    'taggit',     # 新增：标签
    'mdeditor',   # 新增：Markdown编辑器
    # 你的应用
    'knowledge',  # FAQ
    'feedback',  # 留言板
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # 防止跨站攻击
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'AP_knowledge.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # 【重要】指向你的 templates 文件夹
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

# 数据库 (默认使用 sqlite3，无需配置)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 密码验证 (默认即可)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 【重要】国际化设置
LANGUAGE_CODE = 'zh-hans'  # 中文
TIME_ZONE = 'Asia/Shanghai'  # 时区
USE_I18N = True
USE_TZ = True

# 静态文件配置 (CSS/JS)
STATIC_URL = 'static/'
# 新增这行，让 Django 知道去根目录的 static 找文件
STATICFILES_DIRS = [ BASE_DIR / "static" ]
# 默认主键字段类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
X_FRAME_OPTIONS = 'SAMEORIGIN'