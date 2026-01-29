from django import forms
from captcha.fields import CaptchaField
from .models import Comment


class CommentForm(forms.ModelForm):
    captcha = CaptchaField(label="验证码")

    class Meta:
        model = Comment
        fields = ['name', 'email', 'content']  # 包含姓名
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '您的称呼'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@email.com (保密)'}),
            'content': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入您的意见或建议...'}),
        }