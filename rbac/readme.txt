使用步骤：

1. 清除rbac/migrations目录下所有的迁移记录，保留__init__.py


2. 在项目路由系统中注册rbac相关路由
        urlpatterns = [
            ...
            path('rbac/', include('rbac.urls',namespace='rbac')),
        ]


3. 注册app


4. 项目settings中配置：路由自动发现，需要排除的 URL 黑名单
        AUTO_DISCOVER_EXCLUDE = [
            '/admin/.*'
        ]


5. 让业务用户表继承权限的UserInfo类
    rbac:
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

    web:
        from rbac.models import UserInfo as RbacUserInfo

        class UserInfo(RbacUserInfo):
            """
            员工表
            """
            verbose_name_cn = '员工列表'
            nickname = models.CharField(verbose_name='姓名', max_length=16)
            phone = models.CharField(verbose_name='手机号', max_length=32)

            gender_choices = (
                (1, '男'),
                (2, '女'),
            )
            gender = models.IntegerField(verbose_name='性别', choices=gender_choices, default=1)

            depart = models.ForeignKey(verbose_name='部门', to="Department",on_delete=models.CASCADE)

            def __str__(self):
                return self.nickname


6. 执行数据库迁移
    如果，对原有项目使用rbac组件，则需要将rbac里面的字段允许为空后在执行迁移，迁移成功后再进行数据手搓


7. 最终进行rbac中间件的注册，实现权限验证



