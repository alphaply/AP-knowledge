from django.core.management.base import BaseCommand
from django.conf import settings
import os
import re
from knowledge.models import Article, Attachment, Comment


class Command(BaseCommand):
    help = '删除无引用的图片和附件文件'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示要删除的文件，不实际删除',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # 获取所有引用的文件路径
        referenced_files = set()

        # 1. 从Article的content字段中提取图片引用
        for article in Article.objects.all():
            if article.content:
                # 查找<img src="...">标签
                img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
                matches = re.findall(img_pattern, article.content)
                for match in matches:
                    # 转换为相对路径
                    if match.startswith('/media/'):
                        referenced_files.add(match[len('/media/'):])
                    elif match.startswith(settings.MEDIA_URL):
                        referenced_files.add(match[len(settings.MEDIA_URL):])
                    # 处理相对路径
                    elif match.startswith('attachments/') or match.startswith('covers/'):
                        referenced_files.add(match)

        # 2. 从Attachment模型中获取文件路径
        for attachment in Attachment.objects.all():
            if attachment.file:
                referenced_files.add(attachment.file.name)

        # 3. 从Article的cover字段中获取封面图片路径
        for article in Article.objects.all():
            if article.cover:
                referenced_files.add(article.cover.name)

        # 4. 检查其他可能的引用（比如在其他文本字段中）
        # 检查Comment的content字段
        for comment in Comment.objects.all():
            if comment.content:
                img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
                matches = re.findall(img_pattern, comment.content)
                for match in matches:
                    if match.startswith('/media/'):
                        referenced_files.add(match[len('/media/'):])

        # 检查其他可能的引用方式，比如直接的文件名等
        # 这里可以扩展来检查其他模型或字段

        # 扫描media/attachments目录
        media_root = settings.MEDIA_ROOT
        attachments_dir = os.path.join(media_root, 'attachments')

        if not os.path.exists(attachments_dir):
            self.stdout.write('attachments目录不存在')
            return

        all_files = set()
        for root, dirs, files in os.walk(attachments_dir):
            for file in files:
                # 获取相对于media目录的路径
                rel_path = os.path.relpath(os.path.join(root, file), media_root)
                all_files.add(rel_path)

        # 找出无引用的文件
        unreferenced_files = all_files - referenced_files

        if not unreferenced_files:
            self.stdout.write('没有找到无引用的文件')
            return

        self.stdout.write(f'找到 {len(unreferenced_files)} 个无引用文件:')
        for file in sorted(unreferenced_files):
            self.stdout.write(f'  {file}')

        if dry_run:
            self.stdout.write('这是预览模式，没有实际删除文件')
            return

        # 删除文件
        deleted_count = 0
        for file in unreferenced_files:
            full_path = os.path.join(media_root, file)
            try:
                os.remove(full_path)
                deleted_count += 1
                self.stdout.write(f'已删除: {file}')
            except OSError as e:
                self.stdout.write(f'删除失败 {file}: {e}')

        self.stdout.write(f'成功删除 {deleted_count} 个文件')