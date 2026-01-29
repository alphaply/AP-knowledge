from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from taggit.models import Tag
from .models import Article, Category
from .forms import CommentForm
import markdown
from django.utils import timezone


def doc_index(request):
    lang = request.GET.get('lang', 'zh-hans')

    # 热门标签 (Tag Cloud)
    tags = Tag.objects.annotate(num_times=Count('taggit_taggeditem_items')).order_by('-num_times')[:15]

    # 获取根节点分类 (MPTT)
    root_categories = Category.objects.filter(parent=None).order_by('order')

    hot_articles = Article.objects.filter(language=lang, is_public=True).order_by('-views')[:5]

    return render(request, 'knowledge/index.html', {
        'hot_articles': hot_articles,
        'categories': root_categories,
        'tags': tags,
        'current_lang': lang
    })


def doc_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    article.views += 1
    article.save(update_fields=['views'])

    # 处理评论提交
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = article
            # 简单获取IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                comment.ip_address = x_forwarded_for.split(',')[0]
            else:
                comment.ip_address = request.META.get('REMOTE_ADDR')
            comment.save()
            return redirect('doc_detail', pk=pk)
    else:
        comment_form = CommentForm()

    # Markdown
    md = markdown.Markdown(extensions=['markdown.extensions.extra', 'markdown.extensions.toc'])
    article.content_html = md.convert(article.content)
    article.toc = md.toc

    # 获取所有评论
    comments = article.comments.filter(is_public=True)

    # 递归获取左侧导航 (根据当前文章分类展示同级或子级)
    # 这里为了简单，我们展示所有一级分类
    root_categories = Category.objects.filter(parent=None).order_by('order')

    translations = Article.objects.filter(group_id=article.group_id).exclude(id=article.id)

    return render(request, 'knowledge/detail.html', {
        'article': article,
        'root_categories': root_categories,
        'translations': translations,
        'comment_form': comment_form,
        'comments': comments,
    })


# search_view 保持不变
def search_view(request):
    query = request.GET.get('q')
    lang = request.GET.get('lang', 'zh-hans')
    results = []
    if query:
        results = Article.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            language=lang,
            is_public=True
        )
    return render(request, 'knowledge/search.html', {'results': results, 'query': query})