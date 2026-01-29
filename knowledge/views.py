from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.contrib import messages  # 引入消息框架
from taggit.models import Tag
from .models import Article, Category
from .forms import CommentForm
import hashlib
import markdown


def get_gravatar_url(email):
    email_hash = hashlib.md5(email.lower().strip().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s=80"


def doc_index(request):
    tags = Tag.objects.annotate(num_times=Count('taggit_taggeditem_items')).order_by('-num_times')[:15]
    root_categories = Category.objects.filter(parent=None).order_by('order')

    # 显式查询中文标题，或者依赖 modeltranslation 的自动 fallback
    hot_articles = Article.objects.filter(is_public=True).order_by('-views')[:5]

    return render(request, 'knowledge/index.html', {
        'hot_articles': hot_articles,
        'categories': root_categories,
        'tags': tags,
    })


def doc_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    article.views += 1
    article.save(update_fields=['views'])

    # === 处理评论提交 ===
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
            messages.success(request, '评论提交成功！')  # 成功提示
            return redirect('doc_detail', pk=pk)
        else:
            # === 核心修复：添加错误提示 ===
            # 获取具体的表单错误信息
            errors = comment_form.errors.as_text()
            messages.error(request, f'提交失败，请检查验证码或输入内容。\n{errors}')
    else:
        comment_form = CommentForm()

        md = markdown.Markdown(
            extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',  # 这里只写扩展名
            ],
            extension_configs={
                'markdown.extensions.toc': {
                    'title': '文章目录',  # 配置写在这里
                    'toc_depth': '2-4'  # (可选) 只显示 h2 到 h4
                }
            }
        )
    article.content_html = md.convert(article.content)
    article.toc = md.toc  # 将生成的目录存入对象，传给前端

    comments = article.comments.filter(is_public=True)
    for c in comments:
        c.avatar_url = get_gravatar_url(c.email)

    root_categories = Category.objects.filter(parent=None).order_by('order')

    return render(request, 'knowledge/detail.html', {
        'article': article,
        'root_categories': root_categories,
        'comment_form': comment_form,
        'comments': comments,
    })


def search_view(request):
    query = request.GET.get('q')
    results = []
    if query:
        results = Article.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_public=True
        )
    return render(request, 'knowledge/search.html', {'results': results, 'query': query})