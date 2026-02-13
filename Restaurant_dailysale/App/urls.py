from django.urls import path
from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('topbar', views.topbar_view, name='topbar'),
    path('login', views.Logindata, name='login'),
    path('logouts',views.Logouts),
    path('reset_password/<int:user_id>/', views.reset_password, name='reset_password'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('add_manager/', views.add_manager, name='manager_add'),
    path('manager_view', views.manager_view, name='manager_view'),
    path('manager_edit/<int:id>/', views.manager_edit, name='manager_edit'),
    path('manager_delete/<int:id>/', views.manager_delete, name='manager_delete'),
    path('add-staff/', views.add_staff, name='add_staff'),
    path('staff_list/', views.staff_list, name='staff_list'),
    path('edit-staff/<int:id>/', views.edit_staff, name='edit_staff'),
    path('delete-staff/<int:id>/', views.delete_staff, name='delete_staff'),
    

]
