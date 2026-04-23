from django.db import models


# Create your models here.


# 菜单
class Menu(models.Model):
    title = models.CharField(verbose_name='一级菜单标题', max_length=32)
    icon = models.CharField(verbose_name='图标', max_length=64)

    def __str__(self):
        return self.title


# 权限表
class Permission(models.Model):
    title = models.CharField(verbose_name='权限名称', max_length=32)
    url = models.CharField(verbose_name='含正则的URL', max_length=128)
    name = models.CharField(verbose_name='url别名', max_length=32, unique=True)

    pid = models.ForeignKey(verbose_name='非菜单的归属', to='self', null=True, blank=True, on_delete=models.CASCADE,
                            limit_choices_to={'pid__isnull': True}, related_name='parents',
                            help_text='非菜单权限归属的二级菜单')

    menu = models.ForeignKey(verbose_name='所属一级菜单', to='Menu', on_delete=models.CASCADE, null=True, blank=True,
                             help_text='不选表示非菜单')

    def __str__(self):
        return self.title


# 角色表
class Role(models.Model):
    title = models.CharField(verbose_name='角色名称', max_length=32)
    permissions = models.ManyToManyField(verbose_name='权限', to='Permission', blank=True)

    def __str__(self):
        return self.title


# 用户表
class UserInfo(models.Model):
    name = models.CharField(verbose_name='用户名称', max_length=32)
    password = models.CharField(verbose_name='密码', max_length=128)
    email = models.EmailField(verbose_name='邮箱', max_length=32)
    roles = models.ManyToManyField(verbose_name='角色', to=Role, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        # django以后再做数据库迁移时，不再为UserInfo类创建相关的表以及表结构
        # 此类可以当做"父类"，被其他Model类继承。
        abstract = True
