
from app01.models import UserInfo
from stark.service.stark import site, StarkConfig


from django.urls import path
from django.http import HttpResponse






# userinfo表自己的crud类，继承StarkConfig类（有通用的curd功能）
class UserInfoConfig(StarkConfig):

    def func(self):
        return HttpResponse('**m')

    # 自定义其他功能
    def extra_url(self):
        urlpatterns = [
            path('xxx/',self.func,name='fu*c')
        ]
        return urlpatterns



site.register(UserInfo,UserInfoConfig)

