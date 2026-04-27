from rbac import models
from rbac.form.bootstrap import Bootstrap

from django import forms
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError

ICON_LIST = [
    # --- 📊 仪表盘与工作台 (Dashboard) ---
    ['fa-solid fa-house', '首页 <i class="fa-solid fa-house"></i>'],
    ['fa-solid fa-desktop', '控制台 <i class="fa-solid fa-desktop"></i>'],
    ['fa-solid fa-gauge-high', '仪表盘 <i class="fa-solid fa-gauge-high"></i>'],
    ['fa-solid fa-bell', '消息中心 <i class="fa-solid fa-bell"></i>'],
    ['fa-solid fa-briefcase', '我的工作台 <i class="fa-solid fa-briefcase"></i>'],

    # --- 👥 组织与权限 (RBAC & Org) ---
    ['fa-solid fa-users', '用户管理 <i class="fa-solid fa-users"></i>'],
    ['fa-solid fa-id-badge', '员工档案 <i class="fa-solid fa-id-badge"></i>'],
    ['fa-solid fa-user-tie', '角色管理 <i class="fa-solid fa-user-tie"></i>'],
    ['fa-solid fa-user-shield', '权限分配 <i class="fa-solid fa-user-shield"></i>'],
    ['fa-solid fa-sitemap', '部门架构 <i class="fa-solid fa-sitemap"></i>'],
    ['fa-solid fa-address-book', '客户池 <i class="fa-solid fa-address-book"></i>'],

    # --- 🏫 教务与核心业务 (Education & CRM) ---
    ['fa-solid fa-school', '校区管理 <i class="fa-solid fa-school"></i>'],
    ['fa-solid fa-book-open', '课程体系 <i class="fa-solid fa-book-open"></i>'],
    ['fa-solid fa-chalkboard-user', '班级管理 <i class="fa-solid fa-chalkboard-user"></i>'],
    ['fa-solid fa-calendar-check', '上课记录 <i class="fa-solid fa-calendar-check"></i>'],
    ['fa-solid fa-clipboard-list', '跟进记录 <i class="fa-solid fa-clipboard-list"></i>'],
    ['fa-solid fa-stamp', '审批流 <i class="fa-solid fa-stamp"></i>'],

    # --- 💰 数据与财务 (Data & Finance) ---
    ['fa-solid fa-chart-line', '数据看板 <i class="fa-solid fa-chart-line"></i>'],
    ['fa-solid fa-chart-column', '统计分析 <i class="fa-solid fa-chart-column"></i>'],
    ['fa-solid fa-wallet', '财务中心 <i class="fa-solid fa-wallet"></i>'],
    ['fa-solid fa-file-invoice-dollar', '缴费明细 <i class="fa-solid fa-file-invoice-dollar"></i>'],
    ['fa-solid fa-database', '数据仓库 <i class="fa-solid fa-database"></i>'],

    # --- 📁 办公与内容 (Workflow & Content) ---
    ['fa-solid fa-folder-open', '资源目录 <i class="fa-solid fa-folder-open"></i>'],
    ['fa-solid fa-list-check', '任务清单 <i class="fa-solid fa-list-check"></i>'],
    ['fa-solid fa-bullhorn', '营销活动 <i class="fa-solid fa-bullhorn"></i>'],
    ['fa-solid fa-newspaper', '文章资讯 <i class="fa-solid fa-newspaper"></i>'],
    ['fa-solid fa-cloud-arrow-up', '云端文件 <i class="fa-solid fa-cloud-arrow-up"></i>'],
    ['fa-solid fa-box-archive', '库存管理 <i class="fa-solid fa-box-archive"></i>'],

    # --- ⚙️ 系统与运维 (System & Settings) ---
    ['fa-solid fa-sliders', '全局配置 <i class="fa-solid fa-sliders"></i>'],
    ['fa-solid fa-bars-staggered', '菜单设置 <i class="fa-solid fa-bars-staggered"></i>'],
    ['fa-solid fa-shield-halved', '安全风控 <i class="fa-solid fa-shield-halved"></i>'],
    ['fa-solid fa-tags', '字典管理 <i class="fa-solid fa-tags"></i>'],
    ['fa-solid fa-clock-rotate-left', '系统日志 <i class="fa-solid fa-clock-rotate-left"></i>'],
    ['fa-solid fa-trash-can', '回收站 <i class="fa-solid fa-trash-can"></i>'],

    # --- 🛠️ 开发者辅助 (Developer) ---
    ['fa-solid fa-code', '开发者选项 <i class="fa-solid fa-code"></i>'],
    ['fa-solid fa-plug', 'API 接口 <i class="fa-solid fa-plug"></i>'],
    ['fa-solid fa-bug', '异常监控 <i class="fa-solid fa-bug"></i>'],
    ['fa-solid fa-circle-question', '帮助文档 <i class="fa-solid fa-circle-question"></i>'],
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
class SecondMenuModelForm(Bootstrap, forms.ModelForm):
    class Meta:
        model = models.Permission
        exclude = ['pid', ]
        widgets = {
            'menu': forms.Select(attrs={'class': 'tom-select-multiple'}, )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        title = self.cleaned_data.get('title')
        menu = self.cleaned_data.get('menu')

        if not title or not menu:
            return self.cleaned_data

        qs = models.Permission.objects.filter(title=title, menu=menu)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            self.add_error('title', '非菜单权限名重复')

        return self.cleaned_data


# 非菜单权限
class PermissionModelForm(Bootstrap, forms.ModelForm):
    class Meta:
        model = models.Permission
        exclude = ['menu']
        widgets = {
            'pid': forms.Select(attrs={'class': 'tom-select-multiple'})
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
            self.add_error('title', '非菜单权限名重复')

        return self.cleaned_data


# 批量操作权限

class MultiAddPermissionForm(Bootstrap, forms.Form):
    title = forms.CharField(widget=forms.TextInput())
    url = forms.CharField(widget=forms.TextInput())
    name = forms.CharField(widget=forms.TextInput())

    menu_id = forms.ChoiceField(
        choices=[(None, '------'), ],
        widget=forms.Select(attrs={'class': 'tom-select-multiple'}),
        required=False,
    )
    pid_id = forms.ChoiceField(
        choices=[(None, '------'), ],
        widget=forms.Select(attrs={'class': 'tom-select-multiple'}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pid_id'].choices += models.Permission.objects.filter(pid__isnull=True,
                                                                          menu__isnull=False).values_list('id', 'title')
        self.fields['menu_id'].choices += models.Menu.objects.values_list('id', 'title')


class MultiEditPermissionForm(Bootstrap, forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())

    title = forms.CharField(widget=forms.TextInput())
    url = forms.CharField(widget=forms.TextInput())
    name = forms.CharField(widget=forms.TextInput())

    menu_id = forms.ChoiceField(
        choices=[(None, '------'), ],
        widget=forms.Select(attrs={'class': 'tom-select-multiple'}),
        required=False,
    )
    pid_id = forms.ChoiceField(
        choices=[(None, '------'), ],
        widget=forms.Select(attrs={'class': 'tom-select-multiple'}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pid_id'].choices += models.Permission.objects.filter(pid__isnull=True,
                                                                          menu__isnull=False).values_list('id', 'title')
        self.fields['menu_id'].choices += models.Menu.objects.values_list('id', 'title')
