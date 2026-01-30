from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from taggit.models import Tag
from .models import Article, Category
from .forms import CommentForm
import hashlib
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import os
import uuid
from django.utils.timezone import now
import math


def add_watermark(img):
    """添加右下角水印到图片"""
    img = img.convert('RGBA')
    
    # 创建与原图同样大小的透明图层用于绘制水印
    watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark)
    
    # 设置水印文字
    text = "Apmemory"
    try:
        # 在 Windows 上使用系统字体路径
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
        font = ImageFont.truetype(font_path, 20)
    except (IOError, OSError):
        try:
            # 尝试其他常见字体
            font_path = "C:\\Windows\\Fonts\\simsun.ttc"  # 中文字体
            font = ImageFont.truetype(font_path, 20)
        except (IOError, OSError):
            font = ImageFont.load_default()
    
    # 获取文字尺寸
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # 计算水印位置 (右下角)
    margin = 30  # 边距
    x = img.width - text_width - margin
    y = img.height - text_height - margin
    
    # 在指定位置绘制水印文字
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 150))  # 设置适当的透明度
    
    # 将水印合成到原图上
    combined = Image.alpha_composite(img, watermark)
    return combined.convert('RGB')


def ckeditor_upload_view(request):
    """自定义CKEditor图片上传视图，添加水印"""
    if request.method == 'POST' and request.FILES.get('upload'):
        uploaded_file = request.FILES['upload']
        
        # 检查是否是图片
        if not uploaded_file.content_type.startswith('image/'):
            return JsonResponse({'error': {'message': '只允许上传图片文件'}})
        
        # 生成文件名
        ext = os.path.splitext(uploaded_file.name)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        upload_path = os.path.join('attachments', now().strftime('%Y/%m'), filename)
        
        # 打开图片并添加水印
        try:
            img = Image.open(uploaded_file)
            print(f"Original image size: {img.size}, format: {img.format}")  # 调试输出
            img_with_watermark = add_watermark(img)
            print(f"Watermarked image size: {img_with_watermark.size}")  # 调试输出
            
            # 保存到临时文件
            from io import BytesIO
            output = BytesIO()
            img_with_watermark.save(output, format=img.format)
            output.seek(0)
            
            # 保存到存储
            saved_path = default_storage.save(upload_path, ContentFile(output.getvalue()))
            file_url = default_storage.url(saved_path)
            
            print(f"Image saved to: {saved_path}, URL: {file_url}")  # 调试输出
            return JsonResponse({
                'url': file_url
            })
        except Exception as e:
            print(f"Error processing image: {str(e)}")  # 调试输出
            return JsonResponse({'error': {'message': str(e)}})
    
    return JsonResponse({'error': {'message': '无效请求'}})


# 移除 markdown 引用，改用 BeautifulSoup 提取 TOC (可选，或者用前端 JS)
# 这里我们采用前端 JS 生成 TOC，因为 CKEditor 的 HTML 结构比较复杂

def get_gravatar_url(email):
    if not email:
        return ""
    email_hash = hashlib.md5(email.lower().strip().encode('utf-8')).hexdigest()
    return f"https://gravatar.loli.net/avatar/{email_hash}?d=identicon&s=40"


def get_common_context():
    # 标签云
    tags = Tag.objects.annotate(num_times=Count('taggit_taggeditem_items')).order_by('-num_times')[:20]

    # 【核心修复】：必须查询所有分类，recursetree 才能渲染出子级
    root_categories = Category.objects.all().order_by('order')

    # 随机文章
    random_articles = Article.objects.filter(is_public=True).order_by('?')[:5]
    # 热门文章
    hot_articles = Article.objects.filter(is_public=True).order_by('-views')[:5]

    return {
        'tags': tags,
        'categories': root_categories,
        'random_articles': random_articles,
        'hot_articles': hot_articles
    }

def doc_index(request):
    # 首页展示所有文章
    articles_list = Article.objects.filter(is_public=True).order_by('-created_at')

    paginator = Paginator(articles_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 创建分页链接列表
    pagination_links = []
    for i in paginator.page_range:
        pagination_links.append({
            'number': i,
            'url': f'?page={i}',
            'is_active': i == page_obj.number
        })

    context = get_common_context()
    context.update({
        'page_obj': page_obj,
        'pagination_links': pagination_links,
        'title': '最新文档'
    })
    return render(request, 'knowledge/index.html', context)


def category_detail(request, pk):
    """分类文章列表"""
    category = get_object_or_404(Category, pk=pk)
    # 获取该分类及其子分类下的所有文章
    categories = category.get_descendants(include_self=True)
    articles_list = Article.objects.filter(category__in=categories, is_public=True).order_by('-created_at')

    paginator = Paginator(articles_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 创建分页链接列表
    pagination_links = []
    for i in paginator.page_range:
        pagination_links.append({
            'number': i,
            'url': f'?page={i}',
            'is_active': i == page_obj.number
        })

    # === 核心修改：计算需要展开的分类 ID 列表 ===
    # 获取当前分类的所有祖先（包括自己），这些节点的子菜单需要设为 show
    expanded_ids = set(category.get_ancestors(include_self=True).values_list('id', flat=True))

    context = get_common_context()
    context.update({
        'page_obj': page_obj,
        'pagination_links': pagination_links,
        'title': f'分类: {category.name}',
        'current_category': category,
        'expanded_ids': expanded_ids,  # 传给模板
    })
    return render(request, 'knowledge/index.html', context)

def tag_detail(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    articles_list = Article.objects.filter(tags=tag, is_public=True).order_by('-created_at')

    paginator = Paginator(articles_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 创建分页链接列表
    pagination_links = []
    for i in paginator.page_range:
        pagination_links.append({
            'number': i,
            'url': f'?page={i}',
            'is_active': i == page_obj.number
        })

    context = get_common_context()
    context.update({
        'page_obj': page_obj,
        'pagination_links': pagination_links,
        'title': f'标签: {tag.name}'
    })
    return render(request, 'knowledge/index.html', context)


def doc_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    article.views += 1
    article.save(update_fields=['views'])

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = article
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                comment.ip_address = x_forwarded_for.split(',')[0]
            else:
                comment.ip_address = request.META.get('REMOTE_ADDR')
            comment.save()
            messages.success(request, '留言提交成功！')
            return redirect('doc_detail', pk=pk)
        else:
            messages.error(request, '提交失败，请检查输入。')
    else:
        comment_form = CommentForm()

    comments = article.comments.filter(is_public=True)
    for c in comments:
        c.avatar_url = get_gravatar_url(c.email)

    # 过滤出存在的附件
    existing_attachments = []
    for attachment in article.attachments.all():
        # 检查附件是否已经在文章内容中作为图片出现
        # 如果附件路径出现在文章内容中，则不将其作为单独的附件显示
        attachment_path = attachment.file.name.replace('\\', '/')  # 统一路径分隔符
        if attachment_path not in article.content:
            if attachment.file and attachment.file.storage.exists(attachment.file.name):
                # 添加文件大小信息
                try:
                    attachment.file_size = attachment.file.size
                except:
                    attachment.file_size = 0  # 如果无法获取大小，则设置为0
                existing_attachments.append(attachment)
        # 如果文件不存在，则跳过

    context = get_common_context()
    context.update({
        'article': article,
        'comment_form': comment_form,
        'comments': comments,
        'existing_attachments': existing_attachments
    })
    return render(request, 'knowledge/detail.html', context)


def search_view(request):
    query = request.GET.get('q', '').strip()  # 获取并去除首尾空格

    if not query:
        return redirect('index')
    
    results = []

    if query:
        # 搜索逻辑 (支持标题、内容、摘要、标签)
        article_results = Article.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(summary__icontains=query) |
            Q(tags__name__icontains=query),
            is_public=True
        ).distinct()

        # 新增：搜索附件文件名
        attachment_results = Article.objects.filter(
            attachments__name__icontains=query,
            is_public=True
        ).distinct()

        # 合并搜索结果，避免重复
        results = (article_results | attachment_results).distinct().order_by('-views')
    else:
        # 如果没有关键词，返回空列表 (或者你可以选择返回所有)
        results = Article.objects.none()

    # === 增加分页逻辑 ===
    paginator = Paginator(results, 10)  # 每页显示 10 条
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 创建分页链接列表
    pagination_links = []
    for i in paginator.page_range:
        pagination_links.append({
            'number': i,
            'url': f'?q={query}&page={i}',
            'is_active': i == page_obj.number
        })

    return render(request, 'knowledge/search.html', {
        'page_obj': page_obj,  # 传分页对象，不再传 raw list
        'pagination_links': pagination_links,
        'query': query
    })