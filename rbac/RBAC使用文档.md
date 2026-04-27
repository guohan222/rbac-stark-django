# 一、 配置教程

**前戏（配置教程）：**

1. 清除rbac/migrations目录下所有的迁移记录，保留`__init__.py`

2. 注册rbac-app

3. 在项目路由系统中注册rbac相关路由

   ```python
   urlpatterns = [
       ...
       path('rbac/', include('rbac.urls',namespace='rbac')),
   ]
   ```

4. 项目settings中配置相关信息:

   ```python
   # 权限和菜单存放在session中的键
   PERMISSION_SESSION_KEY = 'permission_url_key'
   MENU_SESSION_KEY = 'menu_url_key'
   
   # 业务app中models中userinfo的路径
   USER_MODEL_PATH = 'web.models.UserInfo'
   ```

   ```python
   # 白名单
   VALID_URL = [
       '/login/',
       '/admin/.*'
       
       # 其他可根据需求自定义
   ]
   
   
   # 路由自动发现，需要排除的 URL 名单
   AUTO_DISCOVER_EXCLUDE = [
       '/admin/.*',	
       '/login/',
       '/logout/',
       
       # 其他可根据需求自定义
   ]
   ```

5. 让业务用户表继承权限的UserInfo类

   ```python
   # rbac:
   
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
   ```

   ```python
   # web
   
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
   ```

6. 执行数据库迁移

   ```
   如果，对原有项目使用rbac组件，则需要将rbac里面的字段允许为空后在执行迁移，迁移成功后再进行数据手搓
   ```

7. 配置中间件

   ```
   建议在 正轨步骤进行完成后 进行配置
   ```

   



# 二、使用教程

**正轨（使用教程）：**

1. 添加一级菜单：

   ```
   http://127.0.0.1:8000/rbac/menu/list/
   ```

2. 录入权限信息：

   ```
   http://127.0.0.1:8000/rbac/multi/permissions/
   ```

3. 权限分配：

   ```
   http://127.0.0.1:8000/rbac/distribute/permissions/
   ```

4. 登录进行权限初始化

   ```python
   from rbac.service.init_permission import init_permission
   
   def login(request):
   
       if request.method == 'GET':
           return render(request, 'login.html')
   
       user = request.POST.get('user')
       pwd = request.POST.get('pwd', '')
   
       # 根据用户名和密码去用户表中获取用户对象
       user = models.UserInfo.objects.filter(name=user, password=pwd).first()
       if not user:
           return render(request, 'login.html', {'msg': '用户名或密码错误'})
       request.session['user_info'] = {'id': user.id, 'nickname': user.nickname}
   
       # 用户权限信息的初始化
       init_permission(request,user)
   
       return redirect('stark:web_customer_pub_changelist')
   ```

5. 前端母版的配置

   ```html
   {% load static %}
   {% load rbac %}
   
   
   <link rel="stylesheet" href="{% static 'rbac/css/rbac.css' %}"/>
   
   <script src="{% static 'rbac/js/rbac.js' %}"></script>
   
   
   # 若单独使用该RBAC组件，需要您引入其他的相关配置
   # 因为，所有前端需要的插件 与 相关页面样式 我都归于STARK组件中，所以单独使用需进行配置
   
   # 两组件前端插件一览：
   	1. tomselect插件，我为RBAC、STARK中都有放置
   	2. fontawesome-free-7.2.0-web插件，仅于STARK组件中
   	3. bootstrap-5.3.0-alpha2-dist插件，仅于STARK组件中
   
   # css与js
   	RBAC组件中我仅放置了，菜单展示的相关样式、点击菜单后的行为js
   	STARK组件中我放置了，Antd风格相关样式进行快速搭建现代风格的页面
   	当然，layout母版中也另写了一些样式
   
   ```

6. 菜单的展示

   ```html
   
   ...
   <aside class="left-menu">
       {% menu request %}
   </aside>
   ...
   
   ```

7. 导航条的展示

   ```html
   <nav aria-label="breadcrumb" class="mb-3 bg-white p-3 rounded shadow-sm border-0">
       {% breadcrumb request %}
   </nav>
   ```

8. 权限控制到按钮（推荐方式二）

   ```python
   方式一：	前端利用filter根据别名进行判断是否有这个权限，决定这个按钮是否进行展示
   
   # 这个 filter 是自定义的模板过滤器 
   # 位于：`rbac/templatetags/rbac.py` 里面的 `has_permission` 函数 
   
   示例：
   
   {% load rbac %}
   
   {% if request|has_permission:"stark:web_customer_add" %}
       <a href="{% url 'stark:web_customer_add' %}" class="btn btn-primary">添加</a>
   {% endif %}
   
   ```

   ```python
   方式二：	诸多config类继承PermissionMixins类（权限拦截类）
   
   # 需单独配置PermissionMixins类（不属于任何组件，仅作为工具，粘连RBAC与STARK组件 实现粒度控制到按钮）
   # 放置：web/utils/mixins
   
   
   示例：
   
   # 1. 导入通用组件库
   from stark.service.stark import StarkConfig
   # 2. 导入当前业务线的专属适配胶水
   from web.utils.mixins import PermissionMixins
   
   # 3. 粘连RBAC与STARK组件 实现粒度控制到按钮
   class CustomerConfig(PermissionMixins, StarkConfig):
       list_display = ['name', 'phone']
       
       
       
       
   # 扩展用法：当某张表有特殊的需求时，可以重写该类中的方法：
   	比如：公海客户表里，如果今天是周五，就额外多展示一列『催单倒计时』，其他时间不展示
   
   # 核心思路：先用 super() 让 Mixin 把没权限的按钮剔除，然后再追加当前表独有的逻辑
   
   def get_list_display(self):
       # 1. 先拿 super() 去过一遍权限过滤，把没权限的编辑/删除踢掉
       val = super().get_list_display() 
   
       # 2. 加入你公海特有的动态逻辑
       import datetime
       if datetime.datetime.now().weekday() == 4: # 如果是周五
           val.append(self.display_countdown) # 追加特殊列
   
       return val	
   
   ```
   
   **放置：web/utils/mixins.py，源码如下（核心胶水层）：**
   
   ```python
   from django.conf import settings
   
   
   class PermissionMixins(object):
       """
       权限拦截基类
       连接  Stark 的页面渲染能力 和 RBAC 的权限校验能力
       实现粒度根据权限粒度控制到按钮，代替前端页面使用filter
       """
   
       def has_permission(self,url_name):
           """根据name判断是否具有该权限"""
           # 继承该类的子类config在stark组件中会利用装饰器在config中进行request的封装
           permission_dict = self.request.session.get(settings.PERMISSION_SESSION_KEY)
   
           # 根据别名进行比对
           url_name = f'{self.site.namespace}:{url_name}'
           if permission_dict and url_name in permission_dict:
               return True
           return False
   
       def get_add_btn(self):
           """劫持添加按钮，根据权限决定是否要进行展示，实现粒度控制到按钮"""
           # (注意：Stark 的 url_name 生成通常是 property，不要加括号)
           if self.has_permission(self.get_add_url_name):
               # 在多继承里，super() 不是简单地找“父类”，而是找 MRO 链条里的下一个类
               return super().get_add_btn()
           return ''
   
       def get_list_display(self):
           """劫持操作列，剔除没有权限的编辑和删除按钮"""
   
           # 先去调用 StarkConfig 原本的逻辑，拿到默认要展示的所有列
           value = super().get_list_display()
   
           result = []
           for item in value:
               # 如果是函数或方法 (可调用的对象)
               if callable(item):
                   if item.__name__ == 'display_edit' and not self.has_permission(self.get_change_url_name):
                       continue
                   if item.__name__ == 'display_del' and not self.has_permission(self.get_del_url_name):
                       continue
   
               # 无论是字符串，还是通过了权限校验的函数，都加进来
               result.append(item)
   
           return result
   ```
   
   











