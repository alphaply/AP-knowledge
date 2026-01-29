from django import forms
from captcha.fields import CaptchaField # 引入验证码字段
from .models import Message

class MessageForm(forms.ModelForm):
    captcha = CaptchaField(label="安全验证") # 自动生成图片和输入框

    class Meta:
        model = Message
        fields = ['company_name', 'contact_person', 'contact_info', 'content']
        # 为了配合 Bootstrap，我们要加 class
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入您的企业名称'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_info': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }