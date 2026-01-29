from django import forms
from captcha.fields import CaptchaField
from .models import Comment


class CommentForm(forms.ModelForm):
    captcha = CaptchaField(label="验证码")

    class Meta:
        model = Comment
        fields = ['nickname', 'content']
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '您的昵称'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入评论内容...'}),
        }