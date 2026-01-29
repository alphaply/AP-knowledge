from django.db import models
from taggit.managers import TaggableManager
from mdeditor.fields import MDTextField
import uuid


class Category(models.Model):
    name_zh = models.CharField("分类名(中文)", max_length=50)
    name_en = models.CharField("分类名(英文)", max_length=50, blank=True)
    order = models.IntegerField("排序", default=0)

    class Meta:
        verbose_name = "文档分类"
        verbose_name_plural = verbose_name
        ordering = ['order']

    def __str__(self):
        return self.name_zh


class Article(models.Model):
    LANG_CHOICES = (('zh', '中文'),('zh-hant', '繁體中文'),('en', 'English'))

    # 关联标识：不同语言的同一篇文章，用同一个 group_id 关联
    group_id = models.UUIDField("多语言关联ID", default=uuid.uuid4, editable=True,
                                help_text="将不同语言版本的同一篇文章设为相同的ID")

    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="所属分类")
    language = models.CharField("语言", max_length=10, choices=LANG_CHOICES, default='zh-hant')

    title = models.CharField("标题", max_length=200)
    # 核心：使用 Markdown 字段
    content = MDTextField("文档内容")

    tags = TaggableManager(blank=True)  # 标签功能

    views = models.PositiveIntegerField("浏览量", default=0)  # 用于热门推荐
    is_public = models.BooleanField("是否公开", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "知识文档"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.language}] {self.title}"