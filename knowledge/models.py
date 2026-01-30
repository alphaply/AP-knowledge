from django.db import models
from taggit.managers import TaggableManager
from mptt.models import MPTTModel, TreeForeignKey
# 替换 MartorField 为 CKEditor 5
from django_ckeditor_5.fields import CKEditor5Field
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit
from PIL import Image, ImageDraw, ImageFont
import os
import uuid
from django.utils.timezone import now
import math


# ... (保留 upload_to_uuid 和 TextWatermark 工具类，代码与上次一致) ...
def upload_to_uuid(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('covers', now().strftime('%Y/%m'), filename)


class TextWatermark:
    def __init__(self, text="Apmemory", opacity=100):
        self.text = text
        self.opacity = opacity

    def process(self, img):
        img = img.convert('RGBA')
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default()
        text = self.text
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # 计算旋转后的对角线长度，确保足够容纳文字
        diagonal = int(math.sqrt(text_width ** 2 + text_height ** 2))
        
        # 创建一个小的文本图像，用于旋转
        text_img = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)
        text_draw.text((0, 0), text, font=font, fill=(255, 255, 255, self.opacity))  # 白色半透明文字
        
        # 旋转文本图像 (约-45度倾斜)
        rotated_text = text_img.rotate(-45, expand=1, fillcolor=(0, 0, 0, 0))
        
        # 确定水印位置 (多个重复的水印，覆盖整个图像)
        pos_x_step = diagonal * 2  # 水平间距
        pos_y_step = diagonal * 2  # 垂直间距
        
        # 在原图上多次放置水印
        for offset_x in range(0, img.size[0], pos_x_step):
            for offset_y in range(0, img.size[1], pos_y_step):
                # 计算每个水印的位置
                watermark.paste(rotated_text, (offset_x, offset_y), rotated_text)
                
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

    # 添加摘要字段
    summary = models.TextField("摘要", blank=True, help_text="文章摘要，如果为空则自动从内容前200个字符生成")

    content = CKEditor5Field("文档内容", config_name='extends')

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

    def get_summary(self):
        """获取文章摘要，如果有手动输入的摘要则使用它，否则自动生成"""
        if self.summary:
            return self.summary
        # 如果没有手动输入摘要，则从内容中提取前200个字符作为摘要
        # 去除HTML标签
        from django.utils.html import strip_tags
        clean_content = strip_tags(self.content)
        return clean_content[:200] + "..." if len(clean_content) > 200 else clean_content


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