from django.urls import path
from django.http import HttpResponse


# 通用crud类，另外通过extra可额外自定义操作
class StarkConfig(object):

    def __init__(self, model_class, site):
        self.model_class = model_class
        self.site = site

    # 通用crud操作方法
    def changelist_view(self, request):
        return HttpResponse('list')

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
        self._registry[model_class] = stark_config(model_class,self)
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
