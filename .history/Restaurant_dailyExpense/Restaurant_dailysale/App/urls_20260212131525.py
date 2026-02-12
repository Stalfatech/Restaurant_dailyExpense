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
    path('edit/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('delete/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('history/', views.history_expenses, name='history_expenses'),

    

]
