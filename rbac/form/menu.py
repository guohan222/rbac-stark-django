from rbac import models
from rbac.form.bootstrap import Bootstrap


from django import forms
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError

ICON_LIST = [
    # --- 门户与看板 (Portal) ---
    ['fa-solid fa-house', '首页 <i class="fa-solid fa-house"></i>'],
    ['fa-solid fa-chart-pie', '控制台 <i class="fa-solid fa-chart-pie"></i>'],
    ['fa-solid fa-gauge', '仪表盘 <i class="fa-solid fa-gauge"></i>'],

    # --- 用户与权限 (Auth) ---
    ['fa-solid fa-user-gear', '用户管理 <i class="fa-solid fa-user-gear"></i>'],
    ['fa-solid fa-address-book', '客户中心 <i class="fa-solid fa-address-book"></i>'],
    ['fa-solid fa-user-shield', '权限安全 <i class="fa-solid fa-user-shield"></i>'],
    ['fa-solid fa-id-card-clip', '身份认证 <i class="fa-solid fa-id-card-clip"></i>'],

    # --- 数据与资产 (Data) ---
    ['fa-solid fa-chart-column', '报表统计 <i class="fa-solid fa-chart-column"></i>'],
    ['fa-solid fa-sack-dollar', '财务管理 <i class="fa-solid fa-sack-dollar"></i>'],
    ['fa-solid fa-database', '数据仓库 <i class="fa-solid fa-database"></i>'],
    ['fa-solid fa-file-invoice', '订单管理 <i class="fa-solid fa-file-invoice"></i>'],

    # --- 办公与流程 (Workflow) ---
    ['fa-solid fa-calendar-days', '日程规划 <i class="fa-solid fa-calendar-days"></i>'],
    ['fa-solid fa-envelope-open-text', '消息中心 <i class="fa-solid fa-envelope-open-text"></i>'],
    ['fa-solid fa-list-check', '任务列表 <i class="fa-solid fa-list-check"></i>'],
    ['fa-solid fa-folder-tree', '资源目录 <i class="fa-solid fa-folder-tree"></i>'],

    # --- 配置与工具 (Settings) ---
    ['fa-solid fa-gear', '通用设置 <i class="fa-solid fa-gear"></i>'],
    ['fa-solid fa-screwdriver-wrench', '运维工具 <i class="fa-solid fa-screwdriver-wrench"></i>'],
    ['fa-solid fa-code', '开发者选项 <i class="fa-solid fa-code"></i>'],
    ['fa-solid fa-bug', '系统日志 <i class="fa-solid fa-bug"></i>'],
]
for item in ICON_LIST:
    item[1] = mark_safe(item[1])




# 一级菜单
class MenuModelForm(Bootstrap, forms.ModelForm):
    class Meta:
        model = models.Menu
        fields = '__all__'
        widgets = {
            'icon': forms.RadioSelect(choices=ICON_LIST, attrs={'class': 'icon-radio'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_title(self):
        title = self.cleaned_data['title']
        qs = models.Menu.objects.filter(title=title)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('一级菜单名重复')
        return title




# 二级菜单
class SecondMenuModelForm(Bootstrap,forms.ModelForm):
    class Meta:
        model = models.Permission
        exclude = ['pid',]
        widgets = {
            'menu':forms.Select(attrs={'class':'tom-select-multiple'},)
        }

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def clean(self):
        title = self.cleaned_data.get('title')
        menu = self.cleaned_data.get('menu')

        if not title or not menu:
            return self.cleaned_data

        qs = models.Permission.objects.filter(title=title, menu=menu)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            self.add_error('title','非菜单权限名重复')

        return self.cleaned_data



# 非菜单权限
class PermissionModelForm(Bootstrap,forms.ModelForm):
    class Meta:
        model = models.Permission
        exclude = ['menu']
        widgets = {
            'pid':forms.Select(attrs={'class':'tom-select-multiple'})
        }

    def clean(self):
        title = self.cleaned_data.get('title')
        menu = self.cleaned_data.get('menu')

        if not title or not menu:
            return self.cleaned_data

        qs = models.Permission.objects.filter(title=title, menu=menu)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            self.add_error('title','非菜单权限名重复')

        return self.cleaned_data





# 批量操作权限

class MultiAddPermissionForm(Bootstrap,forms.Form):
    title = forms.CharField(widget=forms.TextInput())
    url = forms.CharField(widget=forms.TextInput())
    name = forms.CharField(widget=forms.TextInput())

    pid = forms.ChoiceField(
        choices=[(None, '------'),],
        widget=forms.Select(attrs={'class':'tom-select-multiple'}),
        required=False,
    )
    menu = forms.ChoiceField(
        choices=[(None,'------'),],
        widget=forms.Select(attrs={'class':'tom-select-multiple'}),
        required=False,
    )

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['pid'].choices += models.Permission.objects.filter(pid__isnull=True,menu__isnull=False).values_list('id','title')
        self.fields['menu'].choices += models.Menu.objects.values_list('id','title')



class MultiEditPermissionForm(Bootstrap,forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())

    title = forms.CharField(widget=forms.TextInput())
    url = forms.CharField(widget=forms.TextInput())
    name = forms.CharField(widget=forms.TextInput())

    pid = forms.ChoiceField(
        choices=[(None, '------'),],
        widget=forms.Select(attrs={'class':'tom-select-multiple'}),
        required=False,
    )
    menu = forms.ChoiceField(
        choices=[(None,'------'),],
        widget=forms.Select(attrs={'class':'tom-select-multiple'}),
        required=False,
    )

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['pid'].choices += models.Permission.objects.filter(pid__isnull=True,menu__isnull=False).values_list('id','title')
        self.fields['menu'].choices += models.Menu.objects.values_list('id','title')