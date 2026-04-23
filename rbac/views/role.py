
from rbac import models
from rbac.form.role import RoleModelForm


from django.shortcuts import render, redirect


# Create your views here.



def role_list(request):
    role_queryset = models.Role.objects.filter().all()
    return render(request,'rbac/role_list.html',{'roles':role_queryset})




def role_add(request):
    if request.method == "GET":
        form =RoleModelForm()
        return render(request,'rbac/change.html',{'form':form})

    form = RoleModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('rbac:role_list')
    return render(request,'rbac/change.html',{'form':form})




def role_edit(request,role_id):
    role_obj = models.Role.objects.filter(pk=role_id).first()
    if not role_obj:
        return redirect('rbac:role_list')

    if request.method == 'GET':
        form = RoleModelForm(instance=role_obj)
        return render(request,'rbac/change.html',{'form':form})

    form = RoleModelForm(data=request.POST,instance=role_obj)
    if form.is_valid():
        form.save()
        return redirect('rbac:role_list')
    return render(request,'rbac/change.html',{'form':form})




def role_del(request,role_id):
    models.Role.objects.filter(pk=role_id).delete()
    return redirect('rbac:role_list')



