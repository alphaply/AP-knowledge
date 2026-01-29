from modeltranslation.translator import register, TranslationOptions
from .models import Article, Category

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',) # 只需要翻译名称

@register(Article)
class ArticleTranslationOptions(TranslationOptions):
    fields = ('title', 'content',) # 标题和内容需要多语言