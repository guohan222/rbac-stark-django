
from app01.models import UserInfo
from stark.service.stark import site, StarkConfig

from django import forms
from django.urls import path
from django.http import HttpResponse






class UserInfoModelForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = '__all__'

    def clean_name(self):
        return self.cleaned_data['name']



# userinfo表自己的crud类，继承StarkConfig类（有通用的curd功能）
class UserInfoConfig(StarkConfig):


    list_display = ['name', 'age', 'email',StarkConfig.display_edit_del]

    # 添加按钮，预留扩展点，例如：根据权限判断是否对其展示此按钮
    # def get_add_btn(self):
    #     return None

    def func(self):
        return HttpResponse('**m')

    # 自定义其他功能
    def extra_url(self):
        urlpatterns = [
            path('xxx/',self.func,name='fu*c')
        ]
        return urlpatterns



site.register(UserInfo,UserInfoConfig)

