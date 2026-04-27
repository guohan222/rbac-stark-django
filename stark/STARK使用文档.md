# 一、配置教程

**前戏（配置教程）：**

1. 拷贝组件，进行app注册（建议先进行STARK组件的套用再进行RBAC组件的套用）

2. 在其他业务app下创建`stark.py`文件，用于对业务表使用通用`CRUD功能与相关路由生成`

   - 注意：RBAC组件不用进行此操作，因为RBAC组件中已写好`CRUD功能`，目的是为了与该组件进行解耦

3. 在项目全局的 `urls.py` 中注册 Stark 引擎的总路由：

   ```python
   from django.contrib import admin
   from django.urls import path, include
   from stark.service.stark import site
   
   
   urlpatterns = [
       path('admin/', admin.site.urls),
       path('rbac/', include('rbac.urls',namespace='rbac')),
       path('stark/', site.urls),
   ]
   ```

   





# 二、使用教程

**正轨（快速使用教程）：**

1. 在业务app中的`stark.py`文件下导入以下内容

   ```python
   # 单例模式，用于进行表的注册与路由的动态生成 与 关联：业务表与对应配置类
   from stark.service.stark import site
   
   # 导入业务app下的models.py文件
   from web import models
   
   
   # 导入表对应的config类，当然如果没有会自动继承STARK组件中的config类
   # 通常自定义对应的config类可对该组件进行业务扩展
   
   以customer表对应的config为例：
   
   from web.views.customer import CustomerConfig,PublicCustomerConfig,PrivateCustomerConfig
   
   ```

2. 进行表的注册与路由动态生成

   ```python
   site.register(models.Customer,CustomerConfig)
   site.register(models.Customer,PublicCustomerConfig,'pub')
   site.register(models.Customer,PrivateCustomerConfig,'pri')
   ```

   ```python
   # Stark 引擎是如何管理多态路由的：
   
   
   						# 自动发现机制 (Autodiscover)：
   > 当把 stark 加入 INSTALLED_APPS 后，项目启动时，Stark 组件会利用 Django 的 autodiscover_modules('stark') 机制，自动扫描并执行每个业务 app 下的 stark.py 文件
   
   
   
   						# 组件核心优化：ModelConfigMapping 对象与多实例复用：
   > 在触发 site.register() 时，Stark 并没有像传统框架那样使用单纯的字典（Dict）来记录注册信息（字典会导致同一张表只能拥有一个配置，键会冲突）
   > 于是我进行了 封装设计：
   > Stark 内部将每一次注册的 (Model类, Config配置类, prefix路由前缀) 封装成一个独立的 ModelConfigMapping 对象，并追加到单例的 _registry 列表中
   
   
   
   						# 彻底打破了“一张表只能有一套增删改查”的限制
   > 例如 Customer 表，可以同时注册 PublicCustomerConfig(prefix='pub') 和 PrivateCustomerConfig(prefix='priv')。底层的 _registry 列表会生成两个独立的 Mapping 对象，最终在路由分发时，根据 prefix 动态派生出两套完全隔离的 URL 和页面逻辑。这完美迎合了复杂企业级应用中“同源数据，多维展现”的业务刚需
   ```

3.  对应配置类使用示例

   ```python
   from stark.form.bootstrap import BootStrap
   from stark.service.stark import StarkConfig, get_choice_text, Option
   
   from web import models
   
   # 导入胶水
   from web.utils.mixins import PermissionMixins
   
   
   from django import forms
   from django.db import transaction
   from django.conf import settings
   from django.http import HttpResponse
   from django.urls import reverse
   from django.utils.safestring import mark_safe
   
   
   
   
   
   class CustomerConfig(StarkConfig):
   
       def display_record(self, obj=None, header=False):
           if header:
               return '跟进记录'
   
           record_url_name = f'stark:web_consultrecord_changelist'
           record_url = reverse(record_url_name)
           return mark_safe(f'<a href="{record_url}?cid={obj.id}">查看跟进</a>'  )
   
       list_display = [
           'name',
           'qq',
           get_choice_text('status', '状态'),
           get_choice_text('gender', '性别'),
           get_choice_text('source', '来源'),
           display_record
       ]
   
       order_by = ['-id']
   
       search_list = ['name', 'qq']
   
       search_group = [
           Option('status', is_choice=True),
           Option('gender', is_choice=True),
           Option('source', is_choice=True),
       ]
   
   
       
   
   # 公户
   class PublicCustomerConfig(PermissionMixins,StarkConfig):
   
       def display_record(self, obj=None, header=False):
           if header:
               return '跟进记录'
   
           record_url_name = f'stark:web_consultrecord_changelist'
           record_url = reverse(record_url_name)
           return mark_safe(f'<a href="{record_url}?cid={obj.id}">查看跟进</a>'  )
   
   
       def get_queryset(self):
           return self.model_class.objects.filter(consultant__isnull=True)
   
       action_list =[]
   
       # 批量申请客户到私户
       def multi_apply(self, request):
           pk_list = request.POST.getlist('pk')
   
           # 假设当前用户id为1
           current_user_id = 1
   
           # 计算当前销售手里 未报名的私户数量
           private_customer_count = models.Customer.objects.filter(consultant_id=current_user_id,status=2).count()
   
           # 判断该销售是否还能继续申请公户到自己手里
           if (private_customer_count + len(pk_list)) > settings.MAX_PRIVATE_CUSTOMER_COUNT:
               return HttpResponse('要这么多干鸡毛')
   
           # 解决“并发抢单”问题，销售 A 和销售 B 同时盯着公海里的“马云”，同时勾选并点击申请，到底算谁的？
           # 加排他锁
           ...
   
   
       multi_apply.text = '批量申请'
       action_list.append(multi_apply)
   
   
       list_display = [
           StarkConfig.display_checkbox,
           'name',
           'qq',
           get_choice_text('status', '状态'),
           get_choice_text('gender', '性别'),
           get_choice_text('source', '来源'),
           display_record
       ]
   
       order_by = ['-id']
   
       search_list = ['name', 'qq']
   
       search_group = [
           Option('status', is_choice=True),
           Option('gender', is_choice=True),
           Option('source', is_choice=True),
       ]
   
   
       
       
    
   
   
   # 私户
   class PrivateModelForm(BootStrap,forms.ModelForm):
       class Meta:
           model = models.Customer
           exclude = ['consultant',]
   
   
   class PrivateCustomerConfig(StarkConfig):
   
       def display_record(self, obj=None, header=False):
           if header:
               return '跟进记录'
   
           record_url_name = f'stark:web_consultrecord_pri_changelist'
           record_url = reverse(record_url_name)
           return mark_safe(f'<a href="{record_url}?cid={obj.id}">查看跟进</a>'  )
   
       def save(self,form,is_modify=True,*args,**kwargs):
           # 假设当前用户id为1
           current_user_id = 1
   
           form.instance.consultant = models.UserInfo.objects.filter(pk=current_user_id).first()
   
           form .save()
   
       def get_queryset(self):
           # 显示当前用户自己的私户
           # 假设当前用户id为1
           current_user_id = 1
           return self.model_class.objects.filter(consultant_id=current_user_id)
   
   
       def get_list_display(self):
           """获取要显示的字段（列），预留的自定义扩展，例如：以后根据用户的不同显示不同的列"""
           val = super().get_list_display()
           val.remove(StarkConfig.display_del)
           return val
   
       action_list = []
   
       # 将客户从私户移除至公户
       def multi_remove(self, request):
           pk_list = request.POST.getlist('pk')
           # 假设当前用户id为1
           current_user_id = 1
           self.model_class.objects.filter(id__in=pk_list,consultant_id=current_user_id,).update(consultant=None)
   
       multi_remove.text = '移除客户'
       action_list.append(multi_remove)
   
   
       model_form_class = PrivateModelForm
   
       list_display = [
           StarkConfig.display_checkbox,
           'name',
           'qq',
           get_choice_text('status','状态'),
           get_choice_text('gender','性别'),
           get_choice_text('source','来源'),
           display_record
       ]
   
       order_by = ['-id']
   
       search_list = ['name','qq']
   
       search_group = [
           Option('status',is_choice=True),
           Option('gender',is_choice=True),
           Option('source',is_choice=True),
       ]
   
   ```







# 三、预留扩展点

Stark 组件在设计上严格遵循了以下软件工程原则：

1. **开闭原则 (OCP)：** 对扩展开放，对修改封闭。所有的钩子方法（如 `get_queryset`, `save`）都是为了让业务方在不改动 Stark 底层代码的情况下，通过类的重写实现多态定制
2. **模板方法模式 (Template Method)：** 父类（`StarkConfig`）定义了增删改查的整体骨架流程，而将具体的执行细节延迟到子类的 Hook 函数中实现
3. **单例模式 (Singleton)：** `StarkSite` 以单例模式运行于内存中，确保全局路由的唯一性和状态共享



**基本说明（扩展规范）：**

1. 组件中会有类似于：

   ```python
       def display_checkbox(self, obj=None, header=False):
           # 自定义要展示的列，然而这个列要想在表中显示肯定要有表head，表body
           # 而表head要显示标题，body要显示数据，
           # 所以在自定义时要区分，什么时候给表head展示指定自定义的标题，什么时候给表body展示自定义的数据
           # 即自定义列的函数要有head与否的区分标识
           if header:
               return '选择'
           return mark_safe(f"<input type='checkbox' name='pk' value='{obj.pk}' />")
   
       def display_edit(self, obj=None, header=False):
           ...
   
       
       
       def get_order_by(self):
          return self.order_by
   
   
   	def get_list_display(self):
           """获取要显示的字段（列），预留的自定义扩展，例如：以后根据用户的不同显示不同的列"""
           value = []
           value.extend(self.list_display)
           value.append(StarkConfig.display_edit)
           value.append(StarkConfig.display_del)
           return value
           
           
           
   1. 如果想自定义表格中展示的列，建议以display_xxx开头
   
   2. 组件中大部分情况下以get_xxx开头的基本上是预留的扩展点，会根据self去对应的config类中找对应的属性或者方法，如果没有则会去基类中找
   
   # 以上基本是组件中预留的扩展点，可根据业务需求进行使用，保证了不仅限于该组件已有的功能，符合对扩展开放，对修改封闭的思想
   
   
   ```

2. 在自定义的 `StarkConfig` 类中，可以直接重写以下静态属性来快速改变页面形态：

   | **配置项**         | **类型** | **作用**                                                     | **示例**                                               |
   | ------------------ | -------- | ------------------------------------------------------------ | ------------------------------------------------------ |
   | `list_display`     | `list`   | 配置表格显示的列，支持普通字段和自定义方法。默认会自动追加编辑、删除按钮。 | `['name', 'phone', StarkConfig.display_edit]`          |
   | `order_by`         | `list`   | 配置 ORM 查询的默认排序规则。                                | `['-id', 'age']`                                       |
   | `search_list`      | `list`   | 开启顶部搜索框，配置允许被关键字（Q对象）进行模糊匹配的字段。 | `['name', 'phone']`                                    |
   | `action_list`      | `list`   | 配置批量操作（如下拉菜单中的“批量删除”），绑定对应的处理函数。 | `[multi_delete, multi_init]`                           |
   | `search_group`     | `list`   | 开启多维度筛选过滤（组合搜索），需实例化 `Option` 对象。     | `[Option('depart'), Option('gender', is_choice=True)]` |
   | `model_form_class` | `class`  | 指定添加/编辑页面使用的自定义 ModelForm，用于精细控制表单样式或校验。 | `MyCustomerModelForm`                                  |





## 1. 视图与路由层扩展

- **`extra_url(self)`**

  - **场景：** 当前表的 CRUD 四个页面不够用了，比如客户表需要增加一个“重置密码”页面、一个“跟进记录”页面
  - **用法：** 重写该方法，返回一个包含额外 URL 规则的列表，当然还需要另外写一个视图函数

  ```Python
  def extra_url(self):
      return [
          path('reset/password/<int:pk>/', self.wrapper(self.reset_password_view), name=self.get_url_name('reset_pwd'))
      ]
  ```

## 2. 数据隔离与查询层扩展 (数据行级权限)

- **`get_queryset(self)`**

  - **场景：** 私海客户表，当前登录的销售只能看他自己的客户，不能看全公司的
  - **用法：** 拦截 ORM 查询，动态加入 `filter` 条件

  ```python
  def get_queryset(self):
      # self.request.session 中有当前登录用户ID
      current_user_id = self.request.session['user_info']['id']
      return self.model_class.objects.filter(consultant_id=current_user_id)
  ```

## 3. UI 与展示层动态扩展

- **`get_list_display(self)`**

  - **场景：** 动态控制列的显示，比如根据 RBAC 权限，剔除“编辑/删除”列（结合 `PermissionMixins`）；或者不同角色的用户看到不同的表格列
  - **用法：** 拿到 `super().get_list_display()` 后进行增删改

- **`get_add_btn(self)`**

  - **场景：** 动态控制左上角“添加按钮”的显示与隐藏，或修改按钮样式

- **自定义列方法 (`display_xxx`)**

  - **场景：** 数据库存的是状态码（1, 2），页面想显示带颜色的标签；或者想在表格里嵌入一个可以弹窗的按钮
  - **用法：** 在类中自定义函数，并加入 `list_display`。

  ```Python
  def display_status(self, obj=None, header=False):
      if header: return '状态'
      color = "green" if obj.status == 1 else "red"
      return mark_safe(f'<span style="color:{color};">{obj.get_status_display()}</span>')
  ```

## 4. 表单与数据保存层扩展

- **`get_model_form_class(self)`**

  - **场景：** 添加和编辑时，想使用完全不同的 `ModelForm`（比如添加时不填密码，编辑时可以填）。可以动态返回

- **`save(self, form, is_modify=True)`**

  - **场景：** 在数据入库前/后的拦截器（前置/后置钩子）。比如：公海客户抢单，销售点击保存时，后台要自动把 `consultant_id` 设为当前登录销售的 ID
  - **用法：**

  ```Python
  def save(self, form, is_modify=True):
      if not is_modify: # 如果是新增操作
          form.instance.consultant_id = self.request.session['user_info']['id']
      form.save() # 最后入库
  ```

## 5. 路由拦截与视图包装扩展 

- **`wrapper(self, func)`**

  - **场景：** 你想给某个特定表的增删改查视图加点“特殊照顾”。比如：客户表的导出功能非常吃内存，你想单独给它加一个**频率限制**或者**缓存**；或者某些特殊的接口想豁免 CSRF 校验
  - **用法：** 它是所有视图函数的“包裹器”。重写它，你可以像写装饰器一样，在视图执行前后插入任意逻辑

  ```Python
  from django.views.decorators.csrf import csrf_exempt
  
  def wrapper(self, func):
      # 让当前类的所有视图都豁免 CSRF 校验
      @csrf_exempt
      def inner(request, *args, **kwargs):
          print("视图执行前：记录日志...")
          res = func(request, *args, **kwargs)
          print("视图执行后：清理垃圾...")
          return res
      return inner
  ```

## 6. 反向解析 URL 扩展 

- **`get_list_url()`, `get_add_url()`, `get_change_url()`, `get_delete_url()`**
  - **场景：** 默认情况下，在“添加”或“编辑”页面点击“保存”或“取消”后，系统会自动跳回**列表页**（`list_url`）。但有时候业务要求：保存完客户信息后，不要跳回列表，而是直接跳到该客户的“详细跟进页面”
  - **用法：** 重写这些方法，直接改变系统底层进行路由反转（`reverse`）时的目标地址

## 7. 搜索与过滤层的动态扩展

除了静态配置 `search_list` 和 `action_list`，Stark 还提供了动态获取的方法：

- **`get_search_list(self)`**

  - **场景：** 普通销售只能按“姓名”搜索客户，而销售主管可以按“手机号、微信、身份证”搜索
  - **用法：** 拦截静态属性，根据当前登录用户的角色，动态返回允许搜索的字段列表

- **`get_action_list(self)`**

  - **场景：** “批量删除”这个极其危险的下拉动作，只有管理员能看到，普通员工下拉框里只有“批量初始化”
  - **用法：**

  ```Python
  def get_action_list(self):
      # 获取原来的批量操作动作
      val = super().get_action_list()
      # 如果不是老板，就把“批量删除”这个动作踢出去
      if self.request.session['role'] != 'CEO':
          val.remove(self.multi_delete)
      return val
  ```

- **`get_order_by(self)`**

  - **场景：** 动态排序。默认按 ID 降序，但如果是“待办事项表”，可以动态调整为按“截止日期”升序

## 8. 组合搜索与多维过滤扩展 

**场景：** 页面顶部需要像京东/淘宝一样，提供多行多列的筛选标签（比如：按性别、按校区、按课程状态筛选），并且支持条件叠加、点击高亮、以及复杂的 URL 参数保持

**核心：`Option` 封装类**

Stark 通过一个极其精妙的 `Option` 类，把复杂的跨表查询和前端渲染抹平了

- **用法：** 在你的 `StarkConfig` 中配置 `search_group` 列表

```Python
from stark.service.v1 import Option

class CustomerConfig(PermissionMixins, StarkConfig):
    # 静态配置组合搜索
    search_group = [
        # 处理 choices 字段
        Option(field='gender', is_choice=True), 
        # 处理 ForeignKey (一对多) 字段
        Option(field='course'), 
        # 处理 ManyToMany (多对多) 字段
        Option(field='tags', is_multi=True), 
        # 自定义数据库取值逻辑 (比如：只想查状态为1的校区)
        Option(field='school', db_condition={'status': 1}) 
    ]
```

**动态扩展钩子 (Hooks)**

如果你不想把过滤条件写死，Stark 依然为你预留了强大的动态干预钩子：

- **`get_search_group(self)`**

  - **场景：** 动态决定当前用户能看到哪些过滤维度。比如：普通销售只能看到“按课程”筛选，而总监还能多看到一行“按销售员”筛选
  - **用法：**

  ```Python
  def get_search_group(self):
      val = []
      val.append(Option('course'))
      # 权限判断：如果是管理层，追加一行过滤项
      if self.request.session.get('role') == 'Manager':
          val.append(Option('consultant'))
      return val
  ```

- **`get_search_group_condition(self, request)`**

  - **场景：** 拦截组合搜索生成的底层 ORM 查询条件字典（通常会配合 Q 对象使用），在最终交给数据库执行前，进行最后一次“偷梁换柱”







# 四、 总结

1. <font color='red'>粗糙点来讲，但凡是组件中的根据self来被调用方法，基本上都可以作为扩展点，当然这说的有些不严谨，但是该STARK组件中大部分是这样，具体情况可阅读该组件，扩展则不一一进行列举</font>
2. <font color='red'>因此阅读STARK组件，会让你收获更多不仅限于此使用文档内的其他功能点</font>

