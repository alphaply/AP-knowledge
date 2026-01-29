from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from knowledge.models import Article, Category
import os
import shutil
import json
import re


class Command(BaseCommand):
    help = '将知识库导出为 Docusaurus 格式 (Markdown/MDX + Static Assets)'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, default='docusaurus_export', help='导出目录')

    def handle(self, *args, **options):
        base_dir = options['output']
        docs_dir = os.path.join(base_dir, 'docs')
        static_media_dir = os.path.join(base_dir, 'static', 'media')

        # 1. 清理旧数据
        if os.path.exists(base_dir):
            self.stdout.write(f"正在清理旧目录: {base_dir}...")
            shutil.rmtree(base_dir)

        os.makedirs(docs_dir)
        os.makedirs(static_media_dir)

        # 2. 复制 Media (图片/附件)
        if os.path.exists(settings.MEDIA_ROOT):
            self.stdout.write("正在搬运静态资源 (Media)...")
            for item in os.listdir(settings.MEDIA_ROOT):
                s = os.path.join(settings.MEDIA_ROOT, item)
                d = os.path.join(static_media_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

        # 3. 递归导出分类和文章
        self.stdout.write("开始导出文档结构...")
        root_categories = Category.objects.filter(parent=None).order_by('order')

        for cat in root_categories:
            self.process_category(cat, docs_dir)

        # 4. 导出未分类文章 (如果有)
        uncategorized_articles = Article.objects.filter(category__isnull=True, is_public=True)
        if uncategorized_articles.exists():
            self.stdout.write("处理未分类文章...")
            other_dir = os.path.join(docs_dir, 'uncategorized')
            os.makedirs(other_dir, exist_ok=True)
            self.create_category_json(other_dir, "未分类文档", 999)
            for art in uncategorized_articles:
                self.create_markdown_file(art, other_dir)

        self.stdout.write(self.style.SUCCESS(
            f'\n导出成功！\n请将 {base_dir}/docs 覆盖到 Docusaurus 的 docs 目录\n请将 {base_dir}/static 覆盖到 Docusaurus 的 static 目录'))

    def process_category(self, category, parent_path):
        """递归处理分类"""
        safe_name = self.sanitize_filename(category.name)
        current_path = os.path.join(parent_path, safe_name)
        os.makedirs(current_path, exist_ok=True)

        self.create_category_json(current_path, category.name, category.order)

        articles = category.article_set.filter(is_public=True).order_by('-created_at')
        for art in articles:
            self.create_markdown_file(art, current_path)

        children = category.children.all().order_by('order')
        for child in children:
            self.process_category(child, current_path)

    def create_category_json(self, path, label, position):
        data = {
            "label": label,
            "position": position,
            "link": {
                "type": "generated-index"
            }
        }
        with open(os.path.join(path, '_category_.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_markdown_file(self, article, path):
        filename = f"{self.sanitize_filename(article.title)}.mdx"
        filepath = os.path.join(path, filename)

        tags = [tag.name for tag in article.tags.all()]

        frontmatter = [
            "---",
            f"title: {article.title}",
            f"sidebar_label: {article.title}",
        ]
        if tags:
            frontmatter.append(f"tags: {json.dumps(tags, ensure_ascii=False)}")

        if article.cover_style == 'show' and article.cover:
            img_path = article.cover.url
            frontmatter.append(f"image: {img_path}")

        frontmatter.append("---\n")

        # === 核心修改：使用 dangerouslySetInnerHTML 包裹 HTML ===
        # 这样 Docusaurus 就不会去校验 HTML 标签是否闭合，也不会报错 style 格式问题
        # 同时完美保留了 CKEditor 的表格合并、颜色等样式

        content = []

        # 1. 封面图 (JSX 方式)
        if article.cover_style == 'show' and article.cover:
            content.append(
                f'<img src="{article.cover.url}" alt="Cover" style={{{{ maxWidth: "100%", borderRadius: "8px", marginBottom: "20px" }}}} />\n')

        # 2. 正文 (原生 HTML 包裹)
        # 这里的 html_content 需要转义反引号 `，防止破坏 JSX 模板字符串
        html_raw = article.content.replace('`', '\\`').replace('${', '\\${')

        # 使用 React 的 dangerouslySetInnerHTML
        content.append(
            'export const RawHtml = ({children}) => (<div dangerouslySetInnerHTML={{__html: children}} />);\n')
        content.append(f'<RawHtml>{{\n`{html_raw}`\n}}</RawHtml>')

        # 3. 附件列表 (JSX 方式)
        attachments = article.attachments.all()
        if attachments.exists():
            content.append('\n\n### 📎 附件下载')
            content.append('<ul>')
            for att in attachments:
                file_size = ""
                try:
                    size_mb = att.file.size / (1024 * 1024)
                    file_size = f" ({size_mb:.2f} MB)"
                except:
                    pass
                content.append(f'<li><a href="{att.file.url}" download target="_blank">{att.name}</a>{file_size}</li>')
            content.append('</ul>')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(frontmatter))
            f.write('\n'.join(content))

        self.stdout.write(f"  - 导出: {article.title}")

    def sanitize_filename(self, name):
        # 替换非法字符，保留中文
        return re.sub(r'[\\/*?:"<>|]', '_', name).strip()