from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from knowledge import views as k_views
from feedback.views import feedback_view
from knowledge.admin import cleanup_media_view

urlpatterns = [
    path('admin/cleanup-media/', cleanup_media_view, name='admin_cleanup_media'),
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),
    path('i18n/', include('django.conf.urls.i18n')),

    path('ckeditor5/image_upload/', k_views.ckeditor_upload_view, name='ckeditor_upload'),
    path('ckeditor5/', include('django_ckeditor_5.urls')),

    path('', k_views.doc_index, name='index'),
    path('category/<int:pk>/', k_views.category_detail, name='category_detail'),
path('tag/<str:slug>/', k_views.tag_detail, name='tag_detail'),
    path('doc/<int:pk>/', k_views.doc_detail, name='doc_detail'),
    path('search/', k_views.search_view, name='search'),
    path('feedback/', feedback_view, name='feedback'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)