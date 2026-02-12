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
    
     path('expenses/', views.dashboard_expenses, name='dashboard_expenses'),
    path('add_expenses/', views.add_expense, name='add_expense'),
    path('edit_expenses/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('delete_expenses/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('history/', views.history_expenses, name='history_expenses'),
    path('supplier/add/', views.add_supplier, name='add_supplier'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/edit/<int:pk>/', views.edit_supplier, name='edit_supplier'),
    path('suppliers/delete/<int:pk>/', views.delete_supplier, name='delete_supplier'),
    path('product/add/', views.add_product, name='add_product'),
    path('no-permission/', views.no_permission, name='no_permission'),
    path('products/', views.product_list, name='product_list'),
path('products/edit/<int:pk>/', views.edit_product, name='edit_product'),
path('products/delete/<int:pk>/', views.delete_product, name='delete_product'),
path('branch/add/', views.add_branch, name='branch_add'),
path('branch/list/', views.branch_list, name='branch_list'),
path('branch/edit/<int:id>/', views.edit_branch, name='branch_edit'),
path('branch/delete/<int:id>/', views.delete_branch, name='branch_delete'),


    

]
