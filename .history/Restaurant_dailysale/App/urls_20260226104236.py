from django.urls import path
from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('topbar', views.topbar_view, name='topbar'),
    path('login', views.Logindata, name='login'),
    path('logouts',views.Logouts, name='logouts'),
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

    path('add-staff/', views.add_staff, name='add_staff'),
    path('staff_list/', views.staff_list, name='staff_list'),
    path('edit-staff/<int:id>/', views.edit_staff, name='edit_staff'),
    path('delete-staff/<int:id>/', views.delete_staff, name='delete_staff'),
    path('staff/', views.adminview_staff, name='adminview_staff'),
    path('daily-sales/', views.daily_sales_dashboard, name='daily_sales_dashboard'),
    path('staff/add/', views.admin_add_staff, name='admin_add_staff'),
    path('staff/edit/<int:id>/', views.admin_edit_staff, name='admin_edit_staff'), 
    path('delete-staff/<int:id>/', views.admindelete_staff, name='delete_staff'),

path('daily-sales/add/', views.add_daily_sale, name='add_daily_sale'),
path('daily-sales/edit/<int:pk>/', views.edit_daily_sale, name='edit_daily_sale'),
path('daily-sales/delete/<int:pk>/', views.delete_daily_sale, name='delete_daily_sale'),
path('sales/history/', views.history_sales, name='history_sales'),
path('delivery-platforms/', views.delivery_platform_list, name='delivery_platform_list'),

    path('delivery-platforms/add/', views.add_delivery_platform, name='add_delivery_platform'),

    path('delivery-platforms/edit/<int:pk>/', views.edit_delivery_platform, name='edit_delivery_platform'),

    path('delivery-platforms/delete/<int:pk>/', views.delete_delivery_platform, name='delete_delivery_platform'),

path('cashbook/', views.cashbook_dashboard, name='cashbook_dashboard'),
path('cashbook/close/<int:branch_id>/<str:date>/',
     views.close_day,
     name='close_day'),
path(
        'cashbook/toggle/<int:branch_id>/<str:date>/',
        views.toggle_day,
        name='toggle_day'
    ),
#salary
    path('salary/add/', views.add_salary, name='add_salary'),
    path('salary/list/', views.salary_list, name='salary_list'),
    path('get_previous_salary_data/', views.get_previous_salary_data, name='get_previous_salary_data'),
    path('salary/edit/<int:pk>/', views.edit_salary, name='edit_salary'),
    path('salary/delete/<int:pk>/', views.delete_salary, name='delete_salary'),
    path('salary/daily/', views.daily_salary_report, name='daily_salary_report'),
    path('monthly-salary-report/', views.monthly_salary_report, name='monthly_salary_report'),
    path('salaries/', views.adminsalary_list, name='admin_salary_list'),
    path('daily-salaries/', views.admindailysalary_list, name='admin_daily_salary_list'),
    path('salary/monthly-report/',views.adminmonthly_salary_report,name='admin_monthly_salary_report'),
    path('salary_add/', views.adminadd_salary, name='admin_add_salary'),
    path('adminsalary/edit/<int:pk>/', views.adminedit_salary, name='admin_edit_salary'),
    path('adminsalary/delete/<int:pk>/', views.admindelete_salary, name='admindelete_salary'),
    path('manager-salary/add/', views.manager_salary, name='manager_salary_add'),
    path("manager-salary/list/",views.manager_salary_list,name="manager_salary_list"),
    path("manager-salary/edit/<int:pk>/",views.manager_salary_edit,name="manager_salary_edit"),
    path('manager-salary/delete/<int:pk>/', views.managerdelete_salary, name='managerdelete_salary'),
    path("manager-monthly-report/",views.manager_monthly_report,name="manager_monthly_report"),
    path(
    "get_previous_manager_salary_data/",
    views.get_previous_manager_salary_data,
    name="get_previous_manager_salary_data"
),path
        'salary/monthly-report/',
        views.adminmonthly_salary_report,
        name='admin_monthly_salary_report'
    ),
    path('delivery-report/', views.delivery_performance_report, name='delivery_report'),

    path('settings/communication/', views.communication_settings_list, name='communication_settings_list'),
path('settings/communication/add/', views.communication_settings_add, name='communication_settings_add'),
path('settings/communication/edit/<int:pk>/', views.communication_settings_edit, name='communication_settings_edit'),
path('settings/communication/delete/<int:pk>/', views.communication_settings_delete, name='communication_settings_delete'),

    path('reports/', views.reports_list, name='reports_list'),

    path('reports/export/<str:report_type>/', views.export_report_page, name='export_report_page'),
    path('reports/send/<str:report_type>/', views.send_report, name='send_report'),









    

]
