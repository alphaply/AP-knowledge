from modeltranslation.translator import register, TranslationOptions
from .models import Article, Category

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',) # 只需要翻译名称

@register(Article)
class ArticleTranslationOptions(TranslationOptions):
    fields = ('title',) # 标题需要多语言，内容不翻译