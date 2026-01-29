from django.db import models
from taggit.managers import TaggableManager
from mptt.models import MPTTModel, TreeForeignKey
from martor.models import MartorField  # 现代化编辑器
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit
# 引入 PIL 用于绘制水印
from PIL import Image, ImageDraw, ImageFont
import os
import uuid
from django.utils.timezone import now


# === 工具函数：图片自动重命名 ===
def upload_to_uuid(instance, filename):
    """
    将上传的文件重命名为 UUID，并按日期归档
    例如: covers/2026/01/550e8400-e29b-41d4-a716-446655440000.jpg
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('covers', now().strftime('%Y/%m'), filename)


# === 自定义处理器：文字水印 ===
class TextWatermark:
    def __init__(self, text="AP Memory", opacity=128):
        self.text = text
        self.opacity = opacity

    def process(self, img):
        # 转换为 RGBA 以支持透明度
        img = img.convert('RGBA')
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)

        # 尝试加载字体，如果失败则使用默认字体 (虽然默认字体很小)
        try:
            # 这里的路径可能需要根据服务器环境调整，Windows一般在 C:/Windows/Fonts/arial.ttf
            font = ImageFont.truetype("arial.ttf", 36)
        except IOError:
            font = ImageFont.load_default()

        # 在右下角绘制水印
        text_width = int(draw.textlength(self.text, font=font))
        text_height = int(font.getbbox("A")[3])  # 近似高度
        x = img.width - text_width - 20
        y = img.height - text_height - 20

        # 绘制半透明文字 (255, 255, 255, 128)
        draw.text((x, y), self.text, font=font, fill=(255, 255, 255, self.opacity))

        # 合并图层
        return Image.alpha_composite(img, watermark).convert('RGB')


# === 1. 多级分类 ===
class Category(MPTTModel):
    # 字段只需要定义一次，translation.py 会自动生成 name_zh_hans, name_en 等
    name = models.CharField("分类名称", max_length=50)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children',
                            verbose_name="上级分类")
    order = models.IntegerField("排序", default=0)

    class MPTTMeta:
        order_insertion_by = ['order']

    class Meta:
        verbose_name = "文档分类"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


# === 2. 知识库文章 (核心) ===
class Article(models.Model):
    category = TreeForeignKey(Category, on_delete=models.CASCADE, verbose_name="所属分类")

    # 标题和内容会自动由 modeltranslation 处理多语言
    title = models.CharField("标题", max_length=200)
    content = MartorField("文档内容")  # 使用 Martor 现代化编辑器

    tags = TaggableManager(blank=True)
    views = models.PositiveIntegerField("浏览量", default=0)
    is_public = models.BooleanField("是否公开", default=True)

    # 封面图 (自动重命名 + 缩放 + 水印)
    cover = ProcessedImageField(
        upload_to=upload_to_uuid,  # 使用上面的重命名函数
        processors=[
            ResizeToFit(800, 600),  # 先缩放
            TextWatermark(text="AP Memory", opacity=150)  # 再加水印
        ],
        format='JPEG',
        options={'quality': 85},
        blank=True, null=True,
        verbose_name="文章封面"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "知识文档"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# === 3. 文章附件 (一对多) ===
class Attachment(models.Model):
    article = models.ForeignKey(Article, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField("文件", upload_to='attachments/%Y/%m/')
    name = models.CharField("显示名称", max_length=100, blank=True, help_text="留空则显示文件名")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "附件"
        verbose_name_plural = verbose_name


# === 4. 评论 (支持邮箱头像) ===
class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')

    # 用户信息
    email = models.EmailField("邮箱", help_text="将作为您的用户名和头像来源")
    # 昵称可选，如果不填就显示邮箱前缀
    nickname = models.CharField("昵称", max_length=50, blank=True)

    content = models.TextField("评论内容")
    admin_reply = models.TextField("管理员回复", blank=True, null=True)

    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField("是否显示", default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "评论"
        verbose_name_plural = verbose_name

    def display_name(self):
        return self.nickname if self.nickname else self.email.split('@')[0]

    def __str__(self):
        return f"{self.email} - {self.content[:20]}"