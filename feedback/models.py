from django.db import models


class Message(models.Model):
    # B2B 关键信息
    company_name = models.CharField("公司名称", max_length=100)
    contact_person = models.CharField("联系人", max_length=50)
    contact_info = models.CharField("联系方式", max_length=100)
    content = models.TextField("需求/留言内容")

    # 系统自动记录的信息
    ip_address = models.GenericIPAddressField("IP地址", blank=True, null=True)
    created_at = models.DateTimeField("提交时间", auto_now_add=True)
    is_handled = models.BooleanField("是否已处理", default=False)

    class Meta:
        verbose_name = "客户留言"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.company_name} - {self.contact_person}"