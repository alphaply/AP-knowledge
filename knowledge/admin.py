from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin  # 引入拖拽排序
from .models import Category, Article, Comment
from django.utils.html import format_html


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    # 使用 mptt 的树状展示
    list_display = ('tree_actions', 'indented_title', 'name_zh', 'name_en')
    list_display_links = ('indented_title',)


class CommentInline(admin.StackedInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at', 'ip_address')
    classes = ['collapse']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'category_name', 'group_id_short', 'attachment_icon')
    list_filter = ('language', 'category', 'is_public')
    search_fields = ('title', 'content')
    inlines = [CommentInline]  # 在文章页直接管理评论

    # 注入 CSS 修复
    class Media:
        css = {'all': ('css/admin_fix.css',)}

    def category_name(self, obj):
        return obj.category.name_zh

    category_name.short_description = "分类"

    def group_id_short(self, obj):
        return str(obj.group_id)[:8] + "..."

    group_id_short.short_description = "关联ID"

    def attachment_icon(self, obj):
        if obj.attachment:
            return "✅ 有"
        return "-"

    attachment_icon.short_description = "附件"

    # === 核心优化：一键复制为其他语言 ===
    actions = ['copy_as_new_lang']

    @admin.action(description='[工具] 复制所选文章(用于创建多语言版)')
    def copy_as_new_lang(self, request, queryset):
        for obj in queryset:
            obj.pk = None  # 清空主键，代表新对象
            obj.title = f"{obj.title} (Copy)"
            obj.is_public = False  # 默认不公开，防误触
            obj.save()
            # 注意：Tags 需要单独复制
        self.message_user(request, f"已复制 {queryset.count()} 篇文章，请进入编辑并修改语言。")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'article', 'short_content', 'admin_reply_status', 'created_at')
    list_filter = ('is_public', 'created_at')
    readonly_fields = ('ip_address', 'created_at')

    def short_content(self, obj):
        return obj.content[:20] + "..."

    def admin_reply_status(self, obj):
        return "✅ 已回" if obj.admin_reply else "❌ 未回"