from django.db import models
from taggit.managers import TaggableManager
from mptt.models import MPTTModel, TreeForeignKey
# 替换 MartorField 为 CKEditor
from ckeditor_uploader.fields import RichTextUploadingField
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit
from PIL import Image, ImageDraw, ImageFont
import os
import uuid
from django.utils.timezone import now


# ... (保留 upload_to_uuid 和 TextWatermark 工具类，代码与上次一致) ...
def upload_to_uuid(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('covers', now().strftime('%Y/%m'), filename)


class TextWatermark:
    def __init__(self, text="AP Memory", opacity=128):
        self.text = text
        self.opacity = opacity

    def process(self, img):
        img = img.convert('RGBA')
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except IOError:
            font = ImageFont.load_default()
        text_width = int(draw.textlength(self.text, font=font))
        text_height = int(font.getbbox("A")[3])
        x = img.width - text_width - 20
        y = img.height - text_height - 20
        draw.text((x, y), self.text, font=font, fill=(255, 255, 255, self.opacity))
        return Image.alpha_composite(img, watermark).convert('RGB')


# === 1. 分类 ===
class Category(MPTTModel):
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


# === 2. 文章 ===
# ... (上面的代码保持不变)

# === 2. 文章 ===
class Article(models.Model):
    # 【修改点】简化为两个选项
    COVER_STYLE_CHOICES = (
        ('none', '不显示封面'),
        ('show', '显示封面'),
    )
    category = TreeForeignKey(Category, on_delete=models.CASCADE, verbose_name="所属分类")
    title = models.CharField("标题", max_length=200)

    content = RichTextUploadingField("文档内容", config_name='default')

    tags = TaggableManager(blank=True)
    views = models.PositiveIntegerField("浏览量", default=0)
    is_public = models.BooleanField("是否公开", default=True)

    cover = ProcessedImageField(
        upload_to=upload_to_uuid,
        processors=[ResizeToFit(1200, 800), TextWatermark()],
        format='JPEG',
        options={'quality': 85},
        blank=True, null=True,
        verbose_name="文章封面"
    )
    # 【修改点】默认值改为 'show'
    cover_style = models.CharField("封面样式", max_length=10, choices=COVER_STYLE_CHOICES, default='show')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "知识文档"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ... (下面的 Attachment 和 Comment 保持不变)

# === 3. 附件 ===
class Attachment(models.Model):
    article = models.ForeignKey(Article, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField("文件", upload_to='attachments/%Y/%m/')
    name = models.CharField("显示名称", max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)


# === 4. 评论 ===
class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField("姓名", max_length=50, default="匿名用户")
    email = models.EmailField("邮箱")
    content = models.TextField("评论内容")
    admin_reply = models.TextField("管理员回复", blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField("是否显示", default=True)

    class Meta:
        ordering = ['-created_at']

    def display_name(self):
        return self.name if self.name else self.email.split('@')[0]