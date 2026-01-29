from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from taggit.models import Tag
from .models import Article, Category
from .forms import CommentForm
import hashlib


# 移除 markdown 引用，改用 BeautifulSoup 提取 TOC (可选，或者用前端 JS)
# 这里我们采用前端 JS 生成 TOC，因为 CKEditor 的 HTML 结构比较复杂

def get_gravatar_url(email):
    email_hash = hashlib.md5(email.lower().strip().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s=80"


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

    context = get_common_context()
    context.update({'page_obj': page_obj, 'title': '最新文档'})
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

    # === 核心修改：计算需要展开的分类 ID 列表 ===
    # 获取当前分类的所有祖先（包括自己），这些节点的子菜单需要设为 show
    expanded_ids = set(category.get_ancestors(include_self=True).values_list('id', flat=True))

    context = get_common_context()
    context.update({
        'page_obj': page_obj,
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

    context = get_common_context()
    context.update({'page_obj': page_obj, 'title': f'标签: {tag.name}'})
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

    context = get_common_context()
    context.update({
        'article': article,
        'comment_form': comment_form,
        'comments': comments,
    })
    return render(request, 'knowledge/detail.html', context)


def search_view(request):
    query = request.GET.get('q', '').strip()  # 获取并去除首尾空格

    if not query:
        return redirect('index')
    results = []

    if query:
        # 搜索逻辑 (支持标题、内容、标签)
        results = Article.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__name__icontains=query),
            is_public=True
        ).distinct().order_by('-views')  # 搜索结果按热度排序，或者用 -created_at
    else:
        # 如果没有关键词，返回空列表 (或者你可以选择返回所有)
        results = Article.objects.none()

    # === 增加分页逻辑 ===
    paginator = Paginator(results, 10)  # 每页显示 10 条
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'knowledge/search.html', {
        'page_obj': page_obj,  # 传分页对象，不再传 raw list
        'query': query
    })