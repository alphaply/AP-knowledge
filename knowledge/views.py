from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Article, Category
import markdown


def doc_index(request):
    """知识中心首页"""
    lang = request.GET.get('lang', 'zh')  # 默认中文

    # 热门推荐 (浏览量前5)
    hot_articles = Article.objects.filter(language=lang, is_public=True).order_by('-views')[:5]

    # 随机推荐 (随机取5个)
    random_articles = Article.objects.filter(language=lang, is_public=True).order_by('?')[:5]

    # 所有分类
    categories = Category.objects.all()

    return render(request, 'knowledge/index.html', {
        'hot_articles': hot_articles,
        'random_articles': random_articles,
        'categories': categories,
        'current_lang': lang
    })


def doc_detail(request, pk):
    """文档详情页"""
    article = get_object_or_404(Article, pk=pk)

    # 浏览量 +1
    article.views += 1
    article.save(update_fields=['views'])

    # Markdown 渲染与 TOC 提取
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
    ])
    article.content_html = md.convert(article.content)
    article.toc = md.toc

    # 左侧导航数据
    categories = Category.objects.all()
    nav_data = []
    for cat in categories:
        articles = Article.objects.filter(category=cat, language=article.language, is_public=True)
        if articles.exists():
            nav_data.append({'cat': cat, 'articles': articles})

    # 获取其他语言版本
    translations = Article.objects.filter(group_id=article.group_id).exclude(id=article.id)

    return render(request, 'knowledge/detail.html', {
        'article': article,
        'nav_data': nav_data,
        'translations': translations,
    })


def search_view(request):
    """搜索"""
    query = request.GET.get('q')
    lang = request.GET.get('lang', 'zh')
    results = []
    if query:
        results = Article.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            language=lang,
            is_public=True
        )
    return render(request, 'knowledge/search.html', {'results': results, 'query': query})