from rbac import models
from rbac.form.bootstrap import Bootstrap

from django import forms
from django.core.exceptions import ValidationError

class RoleModelForm(Bootstrap,forms.ModelForm):

    class Meta:
        model = models.Role
        fields = '__all__'
        widgets = {
            'permissions':forms.SelectMultiple(attrs={'class':'tom-select-multiple'},)
        }

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def clean_title(self):
        title = self.cleaned_data['title']
        qs = models.Role.objects.filter(title=title)

        # 为下面判断是否有重名时，排开自己
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError('角色名重复')
        return title




