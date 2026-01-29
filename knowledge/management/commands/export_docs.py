from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
from django.test import RequestFactory
from knowledge.views import doc_index, doc_detail
from knowledge.models import Article
import os
import shutil


class Command(BaseCommand):
    help = '将知识库导出为静态 HTML 文件 (输出到 dist 目录)'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, default='dist', help='输出目录')

    def handle(self, *args, **options):
        output_dir = options['output']

        # 1. 清理旧数据
        if os.path.exists(output_dir):
            self.stdout.write(f"清理旧目录: {output_dir}...")
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        # 2. 复制静态文件 (Static & Media)
        self.stdout.write("正在复制静态资源...")

        # 复制 static (CSS/JS/Fonts)
        # 注意：这里假设你使用的是开发环境的 static 目录。
        # 如果是生产环境，应该复制 STATIC_ROOT。这里我们遍历 STATICFILES_DIRS。
        static_dest = os.path.join(output_dir, 'static')
        for static_dir in settings.STATICFILES_DIRS:
            if os.path.exists(static_dir):
                shutil.copytree(static_dir, static_dest, dirs_exist_ok=True)

        # 复制 media (上传的图片/附件)
        media_dest = os.path.join(output_dir, 'media')
        if os.path.exists(settings.MEDIA_ROOT):
            shutil.copytree(settings.MEDIA_ROOT, media_dest, dirs_exist_ok=True)

        # 3. 模拟请求并生成页面
        factory = RequestFactory()

        # --- 导出首页 (Index) ---
        self.stdout.write("正在生成首页...")
        request = factory.get('/')
        response = doc_index(request)
        if hasattr(response, 'render'):
            response.render()

        with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(response.content.decode('utf-8'))

        # --- 导出所有文章详情页 ---
        articles = Article.objects.filter(is_public=True)
        total = articles.count()
        self.stdout.write(f"发现 {total} 篇公开文章，开始导出...")

        for i, art in enumerate(articles, 1):
            self.stdout.write(f"[{i}/{total}] 导出文章: {art.title}")

            # 模拟访问 /doc/<id>/
            request = factory.get(f'/doc/{art.id}/')
            response = doc_detail(request, pk=art.id)
            if hasattr(response, 'render'):
                response.render()

            # 为了让 URL /doc/1/ 在静态服务器上有效，我们需要创建 dist/doc/1/index.html
            doc_dir = os.path.join(output_dir, 'doc', str(art.id))
            os.makedirs(doc_dir, exist_ok=True)

            with open(os.path.join(doc_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(response.content.decode('utf-8'))

        self.stdout.write(self.style.SUCCESS(f'\n导出完成！文件位于: {os.path.abspath(output_dir)}'))
        self.stdout.write(self.style.WARNING('注意：静态导出后，评论、搜索、验证码功能将不可用。'))
        self.stdout.write('提示：你可以进入 dist 目录运行 "python -m http.server" 来预览。')