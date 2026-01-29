from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from knowledge import views as k_views
from feedback.views import feedback_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),
    path('i18n/', include('django.conf.urls.i18n')),

    # 替换 martor 为 ckeditor 的上传路由
    path('ckeditor/', include('ckeditor_uploader.urls')),

    path('', k_views.doc_index, name='index'),
    path('category/<int:pk>/', k_views.category_detail, name='category_detail'),
    path('tag/<slug:slug>/', k_views.tag_detail, name='tag_detail'),
    path('doc/<int:pk>/', k_views.doc_detail, name='doc_detail'),
    path('search/', k_views.search_view, name='search'),
    path('feedback/', feedback_view, name='feedback'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)