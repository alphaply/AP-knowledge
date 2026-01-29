from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline  # 多语言支持
from .models import Category, Article, Attachment, Comment


# 1. 分类管理 (多语言 + 树状拖拽)
# 需要同时继承 DraggableMPTTAdmin 和 TranslationAdmin，注意顺序
class CategoryAdmin(DraggableMPTTAdmin, TranslationAdmin):
    list_display = ('tree_actions', 'indented_title',)
    list_display_links = ('indented_title',)


admin.site.register(Category, CategoryAdmin)


# 2. 附件内联 (在文章页直接添加附件)
class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 1


# 3. 评论内联
class CommentInline(admin.StackedInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at', 'ip_address')
    classes = ['collapse']


# 4. 文章管理 (多语言支持)
@admin.register(Article)
class ArticleAdmin(TranslationAdmin):
    list_display = ('title', 'category', 'is_public', 'created_at')
    list_filter = ('category', 'is_public')
    search_fields = ('title', 'content')
    inlines = [AttachmentInline, CommentInline]

    # Martor 编辑器在 Admin 中需要的 Media
    class Media:
        css = {'all': ('css/admin_fix.css',)}  # 之前修 bug 的 css 还是带着比较好


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('email', 'display_name', 'article', 'created_at', 'is_public')