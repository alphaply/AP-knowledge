from django.db import models
from taggit.managers import TaggableManager
from mdeditor.fields import MDTextField
from mptt.models import MPTTModel, TreeForeignKey  # 引入 MPTT
import uuid
import os


# === 1. 多级分类 ===
class Category(MPTTModel):
    name_zh = models.CharField("分类名(简体)", max_length=50)
    name_hant = models.CharField("分类名(繁体)", max_length=50, blank=True)
    name_en = models.CharField("分类名(EN)", max_length=50, blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children',
                            verbose_name="上级分类")
    order = models.IntegerField("排序", default=0)

    class MPTTMeta:
        order_insertion_by = ['order']

    class Meta:
        verbose_name = "文档分类"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name_zh


# === 2. 文章模型 (增加附件) ===
class Article(models.Model):
    LANG_CHOICES = (
        ('zh-hans', '简体中文'),
        ('zh-hant', '繁體中文'),
        ('en', 'English')
    )

    group_id = models.UUIDField("多语言关联ID", default=uuid.uuid4, editable=True,
                                help_text="同一篇文章的不同语言版本请使用相同的ID")
    category = TreeForeignKey(Category, on_delete=models.CASCADE, verbose_name="所属分类")  # 改用 TreeForeignKey
    language = models.CharField("语言", max_length=10, choices=LANG_CHOICES, default='zh-hans')

    title = models.CharField("标题", max_length=200)
    content = MDTextField("文档内容")

    # 【新增】附件功能
    attachment = models.FileField("附件下载", upload_to='attachments/%Y/%m/', blank=True, null=True,
                                  help_text="支持PDF, Docx等格式")

    tags = TaggableManager(blank=True)
    views = models.PositiveIntegerField("浏览量", default=0)
    is_public = models.BooleanField("是否公开", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "知识文档"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_language_display()}] {self.title}"

    def filename(self):
        return os.path.basename(self.attachment.name) if self.attachment else ""


# === 3. 评论模型 (新增) ===
class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', verbose_name="所属文章")
    nickname = models.CharField("昵称", max_length=50, default="游客")
    content = models.TextField("评论内容")

    # 管理员回复
    admin_reply = models.TextField("管理员回复", blank=True, null=True, help_text="在此处填写回复内容，前端将显示给用户")
    reply_at = models.DateTimeField("回复时间", blank=True, null=True)

    ip_address = models.GenericIPAddressField("IP地址", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField("是否显示", default=True)

    class Meta:
        verbose_name = "文章评论"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nickname} @ {self.article.title}"