from django.shortcuts import render, redirect
from django.contrib import messages # 消息闪现
from .forms import MessageForm

def feedback_view(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            # 获取IP地址
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                msg.ip_address = x_forwarded_for.split(',')[0]
            else:
                msg.ip_address = request.META.get('REMOTE_ADDR')
            msg.save()
            messages.success(request, '留言提交成功！我们会尽快联系您。')
            return redirect('index') # 提交成功回首页
        else:
            messages.error(request, '验证码错误或填写不完整。')
    else:
        form = MessageForm()

    return render(request, 'feedback_page.html', {'form': form})