from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 注意这里引入的是 doc_index 等新函数
from knowledge.views import doc_index, doc_detail, search_view
from feedback.views import feedback_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),

    # 【新增 1】语言切换功能的路由 (解决 set_language 报错)
    path('i18n/', include('django.conf.urls.i18n')),

    # 【新增 2】Martor 编辑器的路由 (V3.0 升级)
    path('martor/', include('martor.urls')),

    # 首页
    path('', doc_index, name='index'),

    # 详情页 doc/1/
    path('doc/<int:pk>/', doc_detail, name='doc_detail'),

    # 搜索页
    path('search/', search_view, name='search'),

    # 留言页
    path('feedback/', feedback_view, name='feedback'),
]

# 图片上传配置
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)