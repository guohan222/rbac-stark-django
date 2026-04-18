from types import FunctionType

from django.shortcuts import render
from django.urls import path
from django.http import HttpResponse


# 通用crud类
class StarkConfig(object):
    # 要展示的列（数据库中的字段or自己定义的列）
    # list_display中因为可能有自定义的列，然而这个列要想在表中显示肯定要有表head，表body
    # 而表head要显示标题，body要显示数据，
    # 所以在自定义时要区分，什么时候给表head展示指定自定义的标题，什么时候给表body展示自定义的数据
    # 即自定义列的函数要有head与否的区分标识
    list_display = []

    def __init__(self, model_class, site):
        self.model_class = model_class
        self.site = site

    def get_list_display(self):
        """获取要显示的字段（列），预留的自定义扩展，例如：以后根据用户的不同显示不同的列"""
        value = []
        value.extend(self.list_display)

        return value

    # 通用crud操作方法
    def changelist_view(self, request):
        # 获取要展示的列
        list_display = self.get_list_display()
        # 表中数据
        queryset = self.model_class.objects.all()

        # 表头
        header_list = []
        if list_display:
            for field_or_func in list_display:
                # 区分要展示的列是自定义的还是表中的字段
                if isinstance(field_or_func,FunctionType):
                    # 给自定义列的函数，表示现在函数功能是表头
                    verbose_name = field_or_func(self,obj=None,header=True)
                else:
                    verbose_name = self.model_class._meta.get_field(field_or_func).verbose_name

                header_list.append(verbose_name)
        else:
            # 如果没有指定要展示的列，则展示，该表名、该表查询出来的所有对象（__str__）
            header_list.append(self.model_class._meta.model_name)


        # 表body [[1,gh], [2,ghh],]
        body_list = []
        for row in queryset:
            # 每一行数据
            tr_list = []
            if not list_display:
                tr_list.append(row)
                body_list.append(tr_list)
                continue

            # 反射，获取该对象中要展示的属性（字段） or  自定义列的数据内容
            for field_or_func in list_display:
                if isinstance(field_or_func,FunctionType):
                    tr_list.append(field_or_func(self,obj=row))
                else:
                    tr_list.append(getattr(row, field_or_func))
            body_list.append(tr_list)

        return render(
            request,
            'stark/changelist.html',
            {
                'header_list':header_list,
                'body_list':body_list,

            }
        )














    def add_view(self, request):
        return HttpResponse('add')

    def change_view(self, request, pk):
        return HttpResponse('edit')

    def delete_view(self, request, pk):
        return HttpResponse('del')

    # 为每张表生成crud路由
    def get_urls(self):
        # noinspection PyProtectedMember
        prefix = f'{self.model_class._meta.app_label}_{self.model_class._meta.model_name}'

        urlpatterns = [
            path('list/', self.changelist_view, name=f'{prefix}_changelist'),
            path('add/', self.add_view, name=f'{prefix}_add'),
            path('edit/<int:pk>/', self.change_view, name=f'{prefix}_change'),
            path('del/<int:pk>/', self.delete_view, name=f'{prefix}_del'),
        ]

        # 检测‘自己(self)’的crud类，有没有在extra_url函数中自定义其他功能的url
        extra = self.extra_url()
        urlpatterns.extend(extra)

        return urlpatterns

    def extra_url(self):
        # 该配置类里目前只提供crud
        return []

    @property
    def urls(self):
        return self.get_urls()


# 表的注册，路由的动态生成
class StarkSite(object):
    def __init__(self):
        """
        1. 大字典，对里面的表进行动态路由创建，以及使用通用crud组件
        2. {userinfo类：userinfo对应的crud类对象,role类：role对应的crud类对象}
        """
        self.app_name = 'stark'
        self.namespace = 'stark'
        self._registry = {}

    # 收集所有表对应的model，以及每张表的crud类
    def register(self, model_class, stark_config=None):
        """
        判断表注册时是否有待带自己的crud类，
        没有则用通用的StarkConfig，
        当然如果有带，通过继承也可以使用StarkConfig中有，而自带中没有的方法  —— （因此可在基本crud之外，根据该表的需求自定义其他操作）

        :param model_class: 表对应的模型
        :param stark_config: 每张表对应的自己的crud类
        :return:
        """
        if not stark_config:
            stark_config = StarkConfig

        # ！！！进行实例化
        self._registry[model_class] = stark_config(model_class, self)
        print(self._registry)

    # 给每张表造crud路由
    def get_urls(self):
        """
        目标效果：
            urlpatterns = [
                path('stark/',([
                                    path('app01/userinfo/',([
                                                                path('list/',view,name),
                                                                path('add/',view,name),
                                                                ...
                                                            ],None,None)),
                                    path(),
                                    ...
                               ],appname,namespace))
            ]
        """

        urlpatterns = []
        for model_class, stark_config in self._registry.items():
            # 获取表所在的app名和表对应的类名（小写）
            app_label = model_class._meta.app_label
            model_name = model_class._meta.model_name

            # 示例中第二层
            urlpatterns.append(path(f'{app_label}/{model_name}/', (stark_config.urls, None, None)))

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.namespace


site = StarkSite()
