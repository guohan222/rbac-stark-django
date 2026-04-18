from django.db import models

# Create your models here.

class UserInfo(models.Model):
    """
    用户表
    """
    name = models.CharField(verbose_name='姓名', max_length=32)
    age = models.CharField(verbose_name='年龄', max_length=32)
    email = models.CharField(verbose_name='邮箱', max_length=32)

    def __str__(self):
        return self.name