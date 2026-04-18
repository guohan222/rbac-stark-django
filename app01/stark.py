
from app01.models import UserInfo
from stark.service.stark import site, StarkConfig


from django.urls import path
from django.http import HttpResponse
from django.utils.safestring import mark_safe






# userinfo表自己的crud类，继承StarkConfig类（有通用的curd功能）
class UserInfoConfig(StarkConfig):


    def display_checkbox(self,obj=None,header=False):
        # 自定义要展示的列，然而这个列要想在表中显示肯定要有表head，表body
        # 而表head要显示标题，body要显示数据，
        # 所以在自定义时要区分，什么时候给表head展示指定自定义的标题，什么时候给表body展示自定义的数据
        # 即自定义列的函数要有head与否的区分标识
        if header:
            return '选择'
        return mark_safe(f"<input type='checkbox' name='{obj.pk}' />")


    list_display = [display_checkbox,'name', 'age', 'email']

    def func(self):
        return HttpResponse('**m')

    # 自定义其他功能
    def extra_url(self):
        urlpatterns = [
            path('xxx/',self.func,name='fu*c')
        ]
        return urlpatterns



site.register(UserInfo,UserInfoConfig)

