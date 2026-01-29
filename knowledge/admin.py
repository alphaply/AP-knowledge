from django.contrib import admin
from .models import Category, Article


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_zh', 'name_en', 'order')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'category', 'views', 'group_id')
    list_filter = ('language', 'category')
    search_fields = ('title', 'content')

    class Media:
        css = {
            'all': ('css/admin_fix.css',)
        }