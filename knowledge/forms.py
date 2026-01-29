from django import forms
from captcha.fields import CaptchaField
from .models import Comment


class CommentForm(forms.ModelForm):
    captcha = CaptchaField(label="验证码")

    class Meta:
        model = Comment
        fields = ['email', 'content']  # 只让用户填邮箱和内容，昵称自动处理
        widgets = {
            'email': forms.EmailInput(
                attrs={'class': 'form-control', 'placeholder': 'name@example.com (将作为您的头像来源)'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入您的评论...'}),
        }