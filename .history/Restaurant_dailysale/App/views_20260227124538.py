
from .models import  DeliveryPlatform, User,Register,Manager,Staff,ManagerSalary
from django.contrib.auth.hashers import make_password,check_password
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from datetime import date
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.conf import settings
from .forms import DailySaleItemFormSet, DeliveryFormSet, LoginForm,ForgotPasswordForm,ResetPasswordForm
from django.conf import settings
from django.db import transaction 
from .models import  User,Register,Manager,Branch,Expense,CashBook
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from django.utils.dateparse import parse_date
from calendar import month_name


from django.db.models import Sum
from datetime import date
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import date
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import date
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import date
from .models import Expense, DailySale, CashBook, Branch

def dashboard(request):
    today = date.today()
    user = request.user

    # Get today's expenses and sales based on user type
    if user.user_type == 0:  # Admin
        expenses = Expense.objects.filter(date=today)
        sales = DailySale.objects.filter(date=today)

        monthly_sales_qs = DailySale.objects.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('total_sales')
        ).order_by('month')

        # 🔹 Get CashBook balances branch-wise for admins
        branch_cashbooks = []
        branches = Branch.objects.all().order_by('name')
        for branch in branches:
            cashbook = CashBook.objects.filter(branch=branch, date=today).first()
            branch_cashbooks.append({
                'branch': branch,
                'opening_balance': cashbook.opening_balance if cashbook else 0,
                'closing_balance': cashbook.closing_balance if cashbook else 0,
                'is_closed': cashbook.is_closed if cashbook else False
            })

    elif user.user_type == 1:  # Manager
        expenses = Expense.objects.filter(date=today, branch=user.branch)
        sales = DailySale.objects.filter(date=today, branch=user.branch)

        monthly_sales_qs = DailySale.objects.filter(branch=user.branch).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('total_sales')
        ).order_by('month')

        # Manager only sees their branch
        cashbook = CashBook.objects.filter(branch=user.branch, date=today).first()
        branch_cashbooks = [{
            'branch': user.branch,
            'opening_balance': cashbook.opening_balance if cashbook else 0,
            'closing_balance': cashbook.closing_balance if cashbook else 0,
            'is_closed': cashbook.is_closed if cashbook else False
        }]

    else:
        expenses = Expense.objects.none()
        sales = DailySale.objects.none()
        monthly_sales_qs = []
        branch_cashbooks = []

    # Convert month to ISO string for Chart.js
    monthly_sales = [
        {'month': m['month'].isoformat(), 'total': m['total']}
        for m in monthly_sales_qs
    ]

    # Daily totals
    daily_total = expenses.aggregate(total=Sum('amount'))['total'] or 0
    daily_sales_total = sales.aggregate(total=Sum('total_sales'))['total'] or 0
    net_profit = daily_sales_total - daily_total

    # Totals by category for today's sales
    totals = sales.aggregate(
    total_breakfast=Sum('breakfast_total'),
    total_lunch=Sum('lunch_total'),
    total_dinner=Sum('dinner_total'),
    total_delivery=Sum('delivery_total'),
    total_pos=Sum('pos_amount'),
    total_cash=Sum('cash_sales'),
    total_sales=Sum('total_sales'),
)

    for key in totals:
        totals[key] = totals[key] or 0

    staff_salaries = []

    if user.user_type == 0:  # Admin → all staff
        staffs = Staff.objects.select_related('branch').all().order_by('branch__name', 'name')
    elif user.user_type == 1:  # Manager → only staff in their branch
        staffs = Staff.objects.select_related('branch').filter(branch=user.branch).order_by('name')
    else:
        staffs = []

    for staff in staffs:
        # Sum of all paid amounts for this staff
        total_paid = Salary.objects.filter(
            staff=staff
        ).aggregate(total_paid=Sum('paid_amount'))['total_paid'] or 0

        # Sum of all salary amounts for this staff
        total_salary_amount = Salary.objects.filter(
            staff=staff
        ).aggregate(total_salary=Sum('salary_amount'))['total_salary'] or 0

        balance_to_pay = total_salary_amount - total_paid
        if balance_to_pay < 0:
            balance_to_pay = 0  # safety

        staff_salaries.append({
            'staff': staff,
            'branch': staff.branch,
            'total_salary': total_paid,
            'balance_to_pay': balance_to_pay
        })

    # ---------------- Prepare template context -----------------
    context = {
        'daily_total': daily_total,
        'daily_sales_total': daily_sales_total,
        'net_profit': net_profit,
        'expenses': expenses,
        'sales': sales,
        'totals': totals,
        'monthly_sales': monthly_sales,
        'branch_cashbooks': branch_cashbooks,
        'staff_salaries': staff_salaries,
    }

    return render(request, 'content_dash.html', context)
def topbar_view(request):
    return render(request, 'topbar.html')


def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        contact = request.POST.get('contact')

        # Validation
        if not email or not password:
            return render(request, 'register.html', {
                'error': 'Email and password are required'
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {
                'error': 'Email already exists'
            })

        # Create User
        user = User(
            email=email,
            name=name,
            user_type=0
        )
        user.set_password(password)
        user.save()

        # Create Register profile
        Register.objects.create(
            name=name,
            contact=contact,
            loginid=user
        )

        return redirect('/login')

    return render(request, 'register.html')

@never_cache
def Logindata(request):
    loginform_display = LoginForm()

    if request.method == "POST":
        login_submission = LoginForm(request.POST)

        if login_submission.is_valid():
            email = login_submission.cleaned_data['email']
            password = login_submission.cleaned_data['password']

            user = User.objects.filter(email=email).first()
            user = authenticate(request, email=email, password=password)

            if user is None:
                messages.error(request, 'Invalid email')
                messages.error(request, "Invalid email or password")
                return redirect('login')
               

            if not check_password(password, user.password):
                messages.error(request, 'Invalid password')
                return redirect('login')
            login(request, user) 

            # ✅ Successful login
            request.session['login_id'] = user.id
            request.session['usertype'] = int(user.user_type)

            next_url = request.session.pop('next_url', None)
            if next_url:
                return redirect(next_url)

            # ✅ Role-based redirection
            if user.user_type == 0:
                return redirect('dashboard')

            elif user.user_type == 1:
                return redirect('dashboard')

            elif user.user_type == 2:
                return redirect('employeedash')

            else:
                messages.error(request, 'Invalid user type')
                return redirect('login')

    return render(request, 'login.html', {'logins': loginform_display})


def Logouts(request):
    request.session.flush()  
    return redirect('login')



def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()

            if user:
                reset_link = f"http://127.0.0.1:8000/reset_password/{user.id}/"
                send_mail(
                    'Reset your password',
                    f'Click this link to reset your password: {reset_link}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, "Password reset link sent to your email!")
            else:
                messages.error(request, "Email not found.")

            # ✅ CORRECT redirect
            return redirect('forgot_password')

    else:
        form = ForgotPasswordForm()

    return render(request, 'forget_password.html', {'form': form})


def reset_password(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new = form.cleaned_data['new_password']
            confirm = form.cleaned_data['confirm_password']
            if new == confirm:
                user.password = make_password(new) 
                user.save()
                messages.success(request, "Password reset successfully!")
                return redirect('/login')
            else:
                messages.error(request, "Passwords do not match.")
    else:
        form = ResetPasswordForm()
    return render(request, 'reset_password.html', {'form': form})
from django.core.exceptions import ValidationError
from .validators import phone_validator  # your validators.py

@never_cache
def add_manager(request):
    if request.session.get('usertype') != 0:
        return redirect('no_permission')

    branches = Branch.objects.all()

    if request.method == "POST":
        name = request.POST.get('name')
        phone = (request.POST.get('phone') or "").strip()
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        address = request.POST.get('address')
        joining_date = request.POST.get('joining_date')
        email = request.POST.get('gmail')
        password = request.POST.get('password')
        photo = request.FILES.get('photo')
        branch_id = request.POST.get('branch')

        context = {
            'branches': branches,
            'form_data': request.POST
        }

        # Required fields
        if not all([name, phone, dob, address, joining_date, email, password, branch_id]):
            messages.error(request, "All mandatory fields are required")
            return render(request, 'Admin/add_manager.html', context)

        # 🔴 Phone Validation (FIELD LEVEL)
        try:
            phone_validator(phone)
        except ValidationError as e:
            context['phone_error'] = e.message
            return render(request, 'Admin/add_manager.html', context)

        # Email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return render(request, 'Admin/add_manager.html', context)

        try:
            with transaction.atomic():
                branch = Branch.objects.get(id=branch_id)

                user = User.objects.create_user(
                    email=email,
                    password=password,
                    name=name,
                    user_type=1,
                    branch=branch
                )

                Register.objects.create(
                    name=name,
                    contact=phone,
                    loginid=user
                )

                Manager.objects.create(
                    user=user,
                    phone=phone,
                    dob=dob,
                    gender=gender,
                    address=address,
                    joining_date=joining_date,
                    photo=photo
                )

            messages.success(request, "Manager added successfully")
            return redirect('manager_view')

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return render(request, 'Admin/add_manager.html', context)

    return render(request, 'Admin/add_manager.html', {
        'branches': branches
    })

@never_cache
def manager_view(request):
    search_query = request.GET.get('search', '')

    managers = Manager.objects.select_related('user', 'user__branch').all().order_by('-id')

    if search_query:
        managers = managers.filter(
            Q(user__name__icontains=search_query)
        )

    return render(request, 'Admin/manager_list.html', {
        'managers': managers,
        'search_query': search_query
    })
@never_cache
def manager_delete(request, id):
    manager = get_object_or_404(Manager, id=id)

    if request.method == "POST":
        try:
            manager.user.delete()   # This deletes Manager via CASCADE
            messages.success(request, "Manager deleted successfully")
        except:
            messages.error(request, "Unable to delete manager")
        return redirect('manager_view')

    # GET request → show confirmation page
    return render(request, 'Admin/manager_confirm_delete.html', {'manager': manager})

@never_cache
def manager_edit(request, id):
    if request.session.get('usertype') != 0:
        return redirect('no_permission')

    manager = get_object_or_404(Manager, id=id)
    branches = Branch.objects.all()

    if request.method == "POST":

        name = (request.POST.get('name') or "").strip()
        email = (request.POST.get('email') or "").strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')   
        phone = (request.POST.get('phone') or "").strip()
        dob = request.POST.get('dob') or None
        gender = request.POST.get('gender')
        joining_date = request.POST.get('joining_date') or None
        address = (request.POST.get('address') or "").strip()
        branch_id = request.POST.get('branch')

        # ===== Basic Validation =====
        if not all([name, email, phone, branch_id]):
            messages.error(request, "All mandatory fields are required")
            return render(request, 'Admin/manager_edit.html', {
                'manager': manager,
                'branches': branches,
                'form_data': request.POST
            })

        # ===== Phone Validation (International) =====
        try:
            phone_validator(phone)
        except ValidationError as e:
            return render(request, 'Admin/manager_edit.html', {
                'manager': manager,
                'branches': branches,
                'form_data': request.POST,
                'phone_error': e.message
            })

        try:
            with transaction.atomic():
                branch = Branch.objects.get(id=branch_id)

                # Update User
                manager.user.name = name
                manager.user.email = email
                manager.user.branch = branch
                manager.user.save()

                # Update Manager
                manager.phone = phone
                manager.dob = dob
                manager.gender = gender
                manager.address = address
                manager.joining_date = joining_date

                if request.FILES.get('photo'):
                    manager.photo = request.FILES.get('photo')

                manager.save()

            messages.success(request, "Manager updated successfully")
            return redirect('manager_view')

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return render(request, 'Admin/manager_edit.html', {
                'manager': manager,
                'branches': branches,
                'form_data': request.POST
            })
    if password or confirm_password:
        if password != confirm_password:
        messages.error(request, "Passwords do not match")
        return render(request, 'Admin/manager_edit.html', {
            'manager': manager,
            'branches': branches,
            'form_data': request.POST
        })

    if len(password) < 6:
        messages.error(request, "Password must be at least 6 characters")

    return render(request, 'Admin/manager_edit.html', {
        'manager': manager,
        'branches': branches
    })
    
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import date
from .models import Expense, Supplier, Product
from .forms import ExpenseForm, SupplierForm, ProductForm
from .decorators import admin_or_manager_required
from django.conf import settings
from django.db.models import Sum
from datetime import date



# ================= DASHBOARD =================
from django.shortcuts import render
from django.db.models import Sum
from datetime import date
from .models import Expense
from .decorators import admin_or_manager_required
# views.py
from datetime import datetime, date
from django.db.models import Sum
from django.shortcuts import render
from .models import Expense
from .decorators import admin_or_manager_required

@admin_or_manager_required
def dashboard_expenses(request):
    user = request.user
    selected_date_str = request.GET.get('date')
    branch_name = request.GET.get('branch', '').strip()

    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = None
    else:
        selected_date = None

    # Base queryset
    if user.user_type == 0:  # Admin
        expenses = Expense.objects.all()
        if branch_name:
            expenses = expenses.filter(branch__name__icontains=branch_name)
    else:  # Manager
        expenses = Expense.objects.filter(branch=user.branch)

    if selected_date:
        expenses = expenses.filter(date=selected_date)

    # Daily total
    daily_total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'expenses/dashboard.html', {
        'expenses': expenses,
        'daily_total': daily_total,
        'selected_date': selected_date
    })


# ================= ADD EXPENSE =================
# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from .forms import ExpenseForm
from .models import CashBook
from datetime import date
from .decorators import admin_or_manager_required

# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import date
from .forms import ExpenseForm
from .models import Expense, CashBook
from .decorators import admin_or_manager_required

from django.db.models import Sum
from datetime import date
from decimal import Decimal

from datetime import date

@admin_or_manager_required
def add_expense(request):
    user = request.user

    form = ExpenseForm(request.POST or None, request.FILES or None, user=user)

    if form.is_valid():
        expense = form.save(commit=False)

        # Determine branch
        if user.user_type == 0:  # Admin
            branch = form.cleaned_data.get('branch')
            if not branch:
                messages.info(request, "Please select a branch.")  # light-blue
                return render(request, 'expenses/expense_form.html', {
                    'form': form,
                    'user_type': user.user_type,
                    'page_title': 'Add Expense'
                })
        else:
            branch = user.branch
            if not branch:
                messages.info(request, "You are not assigned to any branch.")  # light-blue
                return redirect('dashboard_expenses')

        # 🔒 Prevent adding for closed day
        if CashBook.objects.filter(
            date=expense.date,
            branch=branch,
            is_closed=True
        ).exists():
            messages.info(request, "Cannot add expense for a closed day.")  # light-blue
            return redirect('dashboard_expenses')

        # Assign branch and status
        expense.branch = branch
        if user.user_type == 0:
            expense.status = form.cleaned_data.get('status') or 'Approved'
        else:
            expense.status = 'Pending'

        expense.created_by = user
        expense.save()

        # 🔄 Update CashBook only if approved
        if expense.status == "Approved":
            update_cashbook(expense.branch, expense.date)

        messages.success(request, "Expense added successfully ✅")
        return redirect('dashboard_expenses')

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'user_type': user.user_type,
        'page_title': 'Add Expense'
    })


from datetime import timedelta


def get_opening_balance(branch, selected_date):
    
    previous_cashbook = CashBook.objects.filter(
        branch=branch,
        date__lt=selected_date
    ).order_by('-date').first()

    if previous_cashbook:
        return previous_cashbook.closing_balance

    return Decimal('0.00')

from decimal import Decimal
from django.db.models import Sum
from .models import CashBook, DailySale, Expense


def update_cashbook(branch, selected_date):

    # 🛑 Safety guard
    if not branch:
        return

    # 🔹 Get or create safely
    cashbook, created = CashBook.objects.get_or_create(
        branch=branch,
        date=selected_date,
        defaults={
            'opening_balance': Decimal('0.00'),
            'cash_sales': Decimal('0.00'),
            'expenses': Decimal('0.00'),
            'closing_balance': Decimal('0.00'),
            'is_closed': False,
        }
    )

    # 🔹 Get previous valid cashbook (exclude null branch)
    previous_cashbook = CashBook.objects.filter(
        branch=branch,
        date__lt=selected_date
    ).exclude(branch__isnull=True).order_by('-date').first()

    if previous_cashbook:
        cashbook.opening_balance = previous_cashbook.closing_balance
    else:
        cashbook.opening_balance = Decimal('0.00')

    # 🔹 Calculate total cash sales
    total_cash = DailySale.objects.filter(
        branch=branch,
        date=selected_date
    ).aggregate(total=Sum('cash_sales'))['total'] or Decimal('0.00')

    # 🔹 Calculate approved expenses
    total_expenses = Expense.objects.filter(
        branch=branch,
        date=selected_date,
        status="Approved"
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    cashbook.cash_sales = total_cash
    cashbook.expenses = total_expenses

    # 🔹 Closing balance formula
    cashbook.closing_balance = (
        cashbook.opening_balance +
        cashbook.cash_sales -
        cashbook.expenses
    )

    cashbook.save()




@admin_or_manager_required
def close_day(request, branch_id, date):

    branch = get_object_or_404(Branch, id=branch_id)

    # Only Admin can close
    if request.user.user_type != 0:
        messages.error(request, "Only Admin can close the day.")
        return redirect('cashbook_dashboard')

    cashbook = CashBook.objects.filter(
        branch=branch,
        date=date
    ).first()

    if not cashbook:
        messages.error(request, "CashBook not found.")
        return redirect('cashbook_dashboard')

    cashbook.is_closed = True
    cashbook.save()

    messages.success(request, f"{date} closed successfully 🔒")
    return redirect('cashbook_dashboard')



# ================= EDIT EXPENSE =================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date
from .forms import ExpenseForm
from .models import Expense, CashBook
from .decorators import admin_or_manager_required

@admin_or_manager_required
def edit_expense(request, pk):

    user = request.user

    if user.user_type == 0:
        expense = get_object_or_404(Expense, pk=pk)
    else:
        expense = get_object_or_404(Expense, pk=pk, branch=user.branch)

    # 🔒 Check if day closed
    if CashBook.objects.filter(
        date=expense.date,
        branch=expense.branch,
        is_closed=True
    ).exists():
        messages.info(request, "Day is closed. Cannot edit expense.")
        return redirect('dashboard_expenses')

    old_status = expense.status
    old_amount = expense.amount
    old_date = expense.date
    old_branch = expense.branch

    form = ExpenseForm(
        request.POST or None,
        request.FILES or None,
        instance=expense,
        user=user
    )

    if form.is_valid():

        updated_expense = form.save(commit=False)

        if user.user_type == 0:
            branch = form.cleaned_data.get('branch')
            if not branch:
                messages.error(request, "Please select a branch.")
                return render(request, 'expenses/expense_form.html', {
                    'form': form,
                    'user_type': user.user_type
                })
            updated_expense.branch = branch
            updated_expense.status = form.cleaned_data.get('status') or updated_expense.status
        else:
            updated_expense.branch = user.branch
            updated_expense.status = expense.status  # manager can't approve

        updated_expense.save()

        # 🔄 IMPORTANT: Recalculate BOTH old and new date
        if old_status == "Approved":
            update_cashbook(old_branch, old_date)

        if updated_expense.status == "Approved":
            update_cashbook(updated_expense.branch, updated_expense.date)

        messages.success(request, "Expense updated successfully.")
        return redirect('dashboard_expenses')

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'user_type': user.user_type,
        'page_title': 'Edit Expense'
    })



# ================= DELETE EXPENSE =================

@admin_or_manager_required
def delete_expense(request, pk):

    expense = get_object_or_404(Expense, pk=pk)

    branch = expense.branch
    expense_date = expense.date
    was_approved = expense.status == "Approved"

    if request.method == "POST":
        expense.delete()

        if was_approved:
            update_cashbook(branch, expense_date)

        messages.success(request, "Expense deleted successfully.")
        return redirect('dashboard_expenses')

    return render(request, 'expenses/delete_confirm.html', {'expense': expense})



# ================= HISTORY =================

@admin_or_manager_required
def history_expenses(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    month = request.GET.get('month')  # e.g., "2026-02"
    branch_name = request.GET.get('branch', '').strip()  # get branch filter

    # Base queryset
    if request.user.user_type == 0:
        expenses = Expense.objects.all()
    else:
        expenses = Expense.objects.filter(branch=request.user.branch)

    # Filter by branch name (for admin only)
    if branch_name and request.user.user_type == 0:
        expenses = expenses.filter(branch__name__icontains=branch_name)

    # Date range filter
    if start and end:
        expenses = expenses.filter(date__range=[start, end])

    # Month filter (overrides date range if provided)
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            expenses = expenses.filter(date__year=year, date__month=month_num)
        except ValueError:
            pass  # ignore invalid month input

    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'expenses/history.html', {
        'expenses': expenses,
        'total': total,
        'selected_month': month,  # optional
    })


@admin_or_manager_required
def approve_expense(request, pk):

    if request.user.user_type != 0:
        return redirect('no_permission')

    expense = get_object_or_404(Expense, pk=pk)

    if CashBook.objects.filter(
        date=expense.date,
        branch=expense.branch,
        is_closed=True
    ).exists():
        messages.error(request, "Day is closed. Cannot approve.")
        return redirect('dashboard_expenses')

    expense.status = 'Approved'
    expense.save()

    # 🔄 Update CashBook
    update_cashbook(expense.branch, expense.date)

    messages.success(request, "Expense Approved ✅")
    return redirect('dashboard_expenses')





# ================= SUPPLIER =================

@login_required
@admin_or_manager_required
def add_supplier(request):
    form = SupplierForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Supplier added successfully.")
        return redirect('supplier_list')
    return render(request, 'expenses/supplier_form.html', {'form': form})


   
from django.db.models import Q 
@admin_or_manager_required
def supplier_list(request):
    query = request.GET.get('q')
    user_type = request.session.get('usertype')
    if user_type == 0:
        suppliers = Supplier.objects.all().order_by('-id')
    else:
     suppliers = Supplier.objects.filter(
        branch=request.user.branch
     ).order_by('-id')


    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query)
        )

    return render(request, 'expenses/supplier_list.html', {
        'suppliers': suppliers,
        'query': query
    })
# ✅ EDIT
@admin_or_manager_required
def edit_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)

    if form.is_valid():
        form.save()
        messages.success(request, "Supplier updated successfully.")
        return redirect('supplier_list')

    return render(request, 'expenses/supplier_form.html', {
        'form': form,
        'edit_mode': True
    })


# ✅ DELETE
@admin_or_manager_required
def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == "POST":
        supplier.delete()
        messages.success(request, "Supplier deleted successfully.")
        return redirect('supplier_list')

    return render(request, 'expenses/supplier_delete.html', {
        'supplier': supplier
    })


# ================= PRODUCT =================

@admin_or_manager_required
def add_product(request):
    form = ProductForm(request.POST or None)
    
    if form.is_valid():
        form.save()
        messages.success(request, "Product added successfully.")  # <-- Success message
        return redirect('product_list')  # <-- Redirect to list or dashboard

    return render(request, 'expenses/product_form.html', {'form': form})
@admin_or_manager_required
def product_list(request):
    query = request.GET.get('q')

    if request.user.user_type == 0:
        products = Product.objects.all()
    else:
     products = Product.objects.filter(
        branch=request.user.branch
     )


    if query:
        products = products.filter(name__icontains=query)

    return render(request, 'expenses/product_list.html', {
        'products': products,
        'query': query
    })
# ✅ EDIT
@admin_or_manager_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)

    if form.is_valid():
        form.save()
        messages.success(request, "Product updated successfully.")
        return redirect('product_list')

    return render(request, 'expenses/product_form.html', {
        'form': form,
        'edit_mode': True
    })


# ✅ DELETE
@admin_or_manager_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect('product_list')

    return render(request, 'expenses/product_delete.html', {
        'product': product
    })
# ================= NO PERMISSION =================
def no_permission(request):
    return render(request, 'no_permission.html')



from .models import Branch
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .decorators import admin_or_manager_required


# ================= ADD BRANCH =================
@admin_or_manager_required
def add_branch(request):

    # Only Admin can add branch
    # if request.user.user_type != 0:
    #     return redirect('no_permission')

    if request.method == "POST":
        name = request.POST.get('name')
        location = request.POST.get('location')

        # Validation
        if not name or not location:
            messages.error(request, "All fields are mandatory")
            return redirect('branch_add')

        if Branch.objects.filter(name=name).exists():
            messages.error(request, "Branch name already exists")
            return redirect('branch_add')

        Branch.objects.create(
            name=name,
            location=location
        )

        messages.success(request, "Branch added successfully")
        return redirect('branch_list')

    return render(request, 'Admin/add_branch.html')


# ================= LIST =================
@admin_or_manager_required
def branch_list(request):

    # if request.user.user_type != 0:
    #     return redirect('no_permission')

    branches = Branch.objects.all().order_by('-id')
    branch_name = request.GET.get('branch')
    if branch_name:
        branches = branches.filter(name__icontains=branch_name)

    return render(request, 'Admin/branch_list.html', {
        'branches': branches
    })


# ================= EDIT =================
@admin_or_manager_required
def edit_branch(request, id):

    # if request.user.user_type != 0:
    #     return redirect('no_permission')

    branch = get_object_or_404(Branch, id=id)

    if request.method == "POST":
        branch.name = request.POST.get('name')
        branch.location = request.POST.get('location')
        branch.save()

        messages.success(request, "Branch updated successfully")
        return redirect('branch_list')

    return render(request, 'Admin/add_branch.html', {
        'branch': branch,
        'edit_mode': True
    })


# ================= DELETE =================
@admin_or_manager_required
def delete_branch(request, id):

    # if request.user.user_type != 0:
    #     return redirect('no_permission')

    branch = get_object_or_404(Branch, id=id)

    if request.method == "POST":
        branch.delete()
        messages.success(request, "Branch deleted successfully")
        return redirect('branch_list')

    return render(request, 'Admin/branch_delete.html', {
        'branch': branch
    })
# ================= staff ================= #

def add_staff(request):
    if request.method == "POST":
        staff_id = request.POST.get('staff_id')
        name = request.POST.get('name')
        gender = request.POST.get('gender')  
        role = request.POST.get('role')
        contact = request.POST.get('contact')
        dob = request.POST.get('dob')
        joining_date = request.POST.get('joining_date')
        salary_type = request.POST.get('salary_type')
        status = request.POST.get('status')

        # Duplicate Staff ID
        if Staff.objects.filter(staff_id=staff_id).exists():
            messages.error(request, "Staff ID already exists.")
            return redirect('add_staff')

        # Contact Validation
        if not contact or not contact.isdigit() or len(contact) != 10:
            messages.error(request, "Contact number must be exactly 10 digits.")
            return redirect('add_staff')
        
        if not gender:
            messages.error(request, "Please select a gender.")
            return redirect('add_staff')

        # DOB Validation
        if dob:
            dob_date = date.fromisoformat(dob)
            if dob_date > date.today():
                messages.error(request, "Date of Birth cannot be in the future.")
                return redirect('add_staff')

        # Get Branch object
        manager_branch = None
        if request.user.branch_id:  # get FK id
            try:
                manager_branch = Branch.objects.get(id=request.user.branch_id)
            except Branch.DoesNotExist:
                manager_branch = None

        # Save Staff
        Staff.objects.create(
            staff_id=staff_id,
            name=name,
            gender=gender,
            role=role,
            contact=contact,
            dob=dob if dob else None,
            joining_date=joining_date,
            salary_type=salary_type,
            status=status,
            branch=manager_branch,  # properly assigned now
            created_by=request.user
        )

        messages.success(request, "Staff added successfully ✅")
        return redirect('staff_list')

    return render(request, 'Manager/staff_add.html')

def staff_list(request):

    user = request.user

    # If Admin → show all staff
    if user.user_type == 0:
        staffs = Staff.objects.all().order_by('id')

    # If Manager → show only their branch staff
    else:
        staffs = Staff.objects.filter(branch=user.branch).order_by('id')

    return render(request, 'Manager/staff_list.html', {
        'staffs': staffs
    })

def staff_list(request):

    user = request.user
    selected_role = request.GET.get('role')

    # 🔹 Base queryset (NO order_by here yet)
    if user.user_type == 0:   # Admin
        base_queryset = Staff.objects.all()
    else:   # Manager
        base_queryset = Staff.objects.filter(branch=user.branch)

    # 🔹 Get distinct roles properly
    roles = base_queryset.values_list('role', flat=True).distinct()

    # 🔹 Apply filtering
    staffs = base_queryset
    if selected_role:
        staffs = staffs.filter(role=selected_role)

    # 🔹 Order at the end
    staffs = staffs.order_by('id')

    return render(request, 'Manager/staff_list.html', {
        'staffs': staffs,
        'roles': roles,
        'selected_role': selected_role
    })


def edit_staff(request, id):

    staff = get_object_or_404(Staff, id=id)

    if request.method == "POST":

        staff_id = request.POST.get('staff_id')
        name = request.POST.get('name')
        gender = request.POST.get('gender')   
        role = request.POST.get('role')
        contact = request.POST.get('contact')
        dob = request.POST.get('dob')
        joining_date = request.POST.get('joining_date')
        salary_type = request.POST.get('salary_type')
        status = request.POST.get('status')

        # Duplicate Staff ID check
        if Staff.objects.filter(staff_id=staff_id).exclude(id=id).exists():
            messages.error(request, "Staff ID already exists.")
            return redirect('edit_staff', id=id)

        # Contact validation
        if not contact or not contact.isdigit() or len(contact) != 10:
            messages.error(request, "Contact number must be exactly 10 digits.")
            return redirect('edit_staff', id=id)

        # DOB validation
        if dob:
            dob_date = date.fromisoformat(dob)
            if dob_date > date.today():
                messages.error(request, "Date of Birth cannot be in the future.")
                return redirect('edit_staff', id=id)

        # Update fields (NO branch update)
        staff.staff_id = staff_id
        staff.name = name
        staff.gender = gender
        staff.role = role
        staff.contact = contact
        staff.dob = dob if dob else None
        staff.joining_date = joining_date
        staff.salary_type = salary_type
        staff.status = status

        staff.save()

        messages.success(request, "Staff updated successfully ✅")
        return redirect('staff_list')

    return render(request, 'Manager/staff_edit.html', {
        'staff': staff
    })

def delete_staff(request, id):
    staff = get_object_or_404(Staff, id=id)

    staff.delete()

    messages.success(request, "Staff deleted successfully 🗑️")
    return redirect('staff_list')


User = get_user_model()


def adminview_staff(request):
    user = request.user

    # Get filter values
    selected_role = request.GET.get('role')
    selected_name = request.GET.get('name')
    selected_branch = request.GET.get('branch')

    # Base queryset
    if user.user_type == 0:  # Admin
        staffs = Staff.objects.select_related('created_by', 'branch').all()
    else:  # Manager
        staffs = Staff.objects.select_related('created_by', 'branch').filter(
            branch=user.branch
        )

    # 🔎 Name filter
    if selected_name:
        staffs = staffs.filter(name__icontains=selected_name)

    # 🎭 Role filter
    if selected_role:
        staffs = staffs.filter(role=selected_role)

    # 🏢 Branch filter (Admin only)
    if selected_branch and user.user_type == 0:
        staffs = staffs.filter(branch_id=selected_branch)

    staffs = staffs.order_by('id')

    # Unique roles for dropdown
    if user.user_type == 0:
        roles = Staff.objects.values_list('role', flat=True).distinct()
        branches = Branch.objects.all()
    else:
        roles = Staff.objects.filter(
            branch=user.branch
        ).values_list('role', flat=True).distinct()
        branches = Branch.objects.filter(id=user.branch.id)

    return render(request, 'Admin/stafflist_view.html', {
        'staffs': staffs,
        'roles': roles,
        'branches': branches,
        'selected_role': selected_role,
        'selected_name': selected_name,
        'selected_branch': selected_branch,
    })


from .models import DailySale, CashBook
from .forms import DailySaleForm
from datetime import date
from django.contrib import messages
from django.db.models import Sum


from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import DailySaleForm, DailySaleItemFormSet, DeliveryFormSet
from .models import DailySale
@admin_or_manager_required
def add_daily_sale(request):
    user = request.user
    sale = DailySale()  # empty instance

    form = DailySaleForm(request.POST or None, user=user, instance=sale)
    item_formset = DailySaleItemFormSet(request.POST or None, prefix='items', instance=sale)
    delivery_formset = DeliveryFormSet(
    request.POST or None,
    prefix='deliveries',
    instance=sale,
    form_kwargs={'user': request.user}   # ✅ PASS USER HERE
)


    if request.method == "POST":
        if form.is_valid() and item_formset.is_valid() and delivery_formset.is_valid():

            # Determine branch
            if user.user_type == 0:  # Admin
                branch = form.cleaned_data.get('branch')
                if not branch:
                    messages.info(request, "Please select a branch.")
                    return render(request, 'sales/daily_sale_form.html', {
                        'form': form,
                        'item_formset': item_formset,
                        'delivery_formset': delivery_formset,
                        'page_title': 'Add Daily Sale',
                        'user_type': user.user_type
                    })
            else:
                branch = user.branch
                if not branch:
                    messages.info(request, "You are not assigned to any branch.")
                    return redirect('daily_sales_dashboard')

            sale_date = form.cleaned_data.get('date')

            # 🔒 Prevent adding for closed day
            if CashBook.objects.filter(
                date=sale_date,
                branch=branch,
                is_closed=True
            ).exists():
                messages.info(request, "Cannot add daily sale for a closed day.")
                return redirect('daily_sales_dashboard')

            # ✅ Save main sale
            sale = form.save(commit=False)
            sale.branch = branch
            sale.created_by = user
            sale.save()

            # Assign saved instance to formsets
            item_formset.instance = sale
            delivery_formset.instance = sale
            

            item_formset.save()
            delivery_formset.save()

            # Recalculate totals
            sale.calculate_totals()
            sale.save(update_fields=[
                'breakfast_total', 'lunch_total', 'dinner_total',
                'delivery_total', 'cash_sales', 'total_sales'
            ])

            update_cashbook(sale.branch, sale.date)

            messages.success(request, "Daily Sale Added Successfully ✅")
            return redirect('daily_sales_dashboard')

        else:
            print("Form errors:", form.errors)
            print("Item formset errors:", item_formset.errors)
            print("Delivery formset errors:", delivery_formset.errors)

    return render(request, 'sales/daily_sale_form.html', {
        'form': form,
        'item_formset': item_formset,
        'delivery_formset': delivery_formset,
        'page_title': 'Add Daily Sale',
        'user_type': user.user_type
    })



from django.db.models import Sum
from datetime import datetime, date
from django.db.models import Sum, Prefetch
from .models import DailySale, DailySaleItem

@admin_or_manager_required
def daily_sales_dashboard(request):

    selected_date = request.GET.get('date')

    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    user = request.user
    branch_name = request.GET.get('branch')

    # ======================
    # ADMIN
    # ======================
    if user.user_type == 0:
        sales = DailySale.objects.filter(date=selected_date)

        if branch_name:
            sales = sales.filter(branch__name__icontains=branch_name)

    # ======================
    # MANAGER
    # ======================
    else:
        if not user.branch:
            sales = DailySale.objects.none()
        else:
            sales = DailySale.objects.filter(
                date=selected_date,
                branch=user.branch
            )

    # 🔥 VERY IMPORTANT (Performance Fix)
    sales = sales.prefetch_related('items')

    # ======================
    # TOTALS
    # ======================
    totals = sales.aggregate(
        total_breakfast=Sum('breakfast_total'),
        total_lunch=Sum('lunch_total'),
        total_dinner=Sum('dinner_total'),
        total_delivery=Sum('delivery_total'),
        total_pos=Sum('pos_amount'),
        total_cash=Sum('cash_sales'),
        total_sales=Sum('total_sales'),
    )

    totals = {k: v or 0 for k, v in totals.items()}

    # ======================
    # PREPARE ITEM STRINGS
    # ======================
    for sale in sales:
        sale.breakfast_items = ", ".join(
            sale.items.filter(meal_type="Breakfast")
            .values_list("item_name", flat=True)
        )

        sale.lunch_items = ", ".join(
            sale.items.filter(meal_type="Lunch")
            .values_list("item_name", flat=True)
        )

        sale.dinner_items = ", ".join(
            sale.items.filter(meal_type="Dinner")
            .values_list("item_name", flat=True)
        )

    return render(request, 'sales/daily_dashboard.html', {
        'sales': sales,
        'totals': totals,
        'selected_date': selected_date,
    })

@admin_or_manager_required
def edit_daily_sale(request, pk):

    sale = get_object_or_404(DailySale, pk=pk)
    user = request.user

    # 🔒 BLOCK IF DAY IS CLOSED
    if CashBook.objects.filter(
        date=sale.date,
        branch=sale.branch,
        is_closed=True
    ).exists():
        messages.info(request, "Day is closed. Cannot edit Daily Sale.")
        return redirect('daily_sales_dashboard')

    form = DailySaleForm(
        request.POST or None,
        instance=sale,
        user=user
    )

    item_formset = DailySaleItemFormSet(
        request.POST or None,
        instance=sale,
        prefix='items'
    )

    delivery_formset = DeliveryFormSet(
        request.POST or None,
        instance=sale,
        prefix='deliveries'
    )

    if request.method == "POST":

        if form.is_valid() and item_formset.is_valid() and delivery_formset.is_valid():

            old_date = sale.date
            old_branch = sale.branch

            sale = form.save(commit=False)

            if user.user_type == 0:
                sale.branch = form.cleaned_data.get('branch')
            else:
                sale.branch = user.branch

            sale.save()

            item_formset.instance = sale
            item_formset.save()

            delivery_formset.instance = sale
            delivery_formset.save()

            sale.calculate_totals()
            sale.save()

            # 🔄 Recalculate old and new date cashbook
            update_cashbook(old_branch, old_date)
            update_cashbook(sale.branch, sale.date)

            messages.success(request, "Sale Updated Successfully ✅")
            return redirect('daily_sales_dashboard')

        else:
            print("FORM ERRORS:", form.errors)
            print("ITEM ERRORS:", item_formset.errors)
            print("DELIVERY ERRORS:", delivery_formset.errors)

    return render(request, 'sales/daily_sale_form.html', {
        'form': form,
        'item_formset': item_formset,
        'delivery_formset': delivery_formset,
        'page_title': 'Edit Daily Sale',
        'user_type': user.user_type
    })


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db import transaction

@admin_or_manager_required
def delete_daily_sale(request, pk):

    user = request.user
    sale = get_object_or_404(DailySale, pk=pk)

    # 🔐 Permission check
    if user.user_type != 0 and sale.branch != user.branch:
        messages.error(request, "You are not allowed to delete this sale.")
        return redirect('daily_sales_dashboard')

    # 🔒 Prevent delete if day closed
    if CashBook.objects.filter(
        date=sale.date,
        branch=sale.branch,
        is_closed=True
    ).exists():
        messages.error(request, "Day is closed. Cannot delete sales.")
        return redirect('daily_sales_dashboard')

    sale_date = sale.date
    sale_branch = sale.branch

    if request.method == "POST":

        with transaction.atomic():

            # 🔹 This automatically deletes:
            # - DailySaleItem (meal items)
            # - DeliverySale (platform entries)
            # Because of on_delete=models.CASCADE
            sale.delete()

            # 🔄 Recalculate cashbook
            update_cashbook(sale_branch, sale_date)

        messages.success(request, "Daily sale deleted successfully ✅")
        return redirect('daily_sales_dashboard')

    return render(request, 'sales/delete_daily_sale.html', {
        'sale': sale
    })




from django.db.models import Sum
from datetime import datetime
from .models import DailySale, DailySaleItem

@admin_or_manager_required
def history_sales(request):

    start = request.GET.get('start')
    end = request.GET.get('end')
    month = request.GET.get('month')
    branch_name = request.GET.get('branch')

    user = request.user

    # Admin → All branches
    if user.user_type == 0:
        sales = DailySale.objects.all()
        if branch_name:
            sales = sales.filter(branch__name__icontains=branch_name)
    else:
        if not user.branch:
            sales = DailySale.objects.none()
        else:
            sales = DailySale.objects.filter(branch=user.branch)

    # Month filter (priority)
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            sales = sales.filter(date__year=year, date__month=month_num)
        except ValueError:
            pass

    # Date range filter
    elif start and end:
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            sales = sales.filter(date__range=[start_date, end_date])
        except ValueError:
            pass

    totals = sales.aggregate(
        total_breakfast=Sum('breakfast_total'),
        total_lunch=Sum('lunch_total'),
        total_dinner=Sum('dinner_total'),
        total_delivery=Sum('delivery_total'),
        total_pos=Sum('pos_amount'),
        total_sales=Sum('total_sales'),
    )

    # Replace None with 0
    for key in totals:
        totals[key] = totals[key] or 0

    # 🔥 Collect item names for selected sales
    all_items = DailySaleItem.objects.filter(sale__in=sales)

    totals['breakfast_items'] = ", ".join(
        all_items.filter(meal_type='Breakfast')
        .values_list('item_name', flat=True)
        .distinct()
    )

    totals['lunch_items'] = ", ".join(
        all_items.filter(meal_type='Lunch')
        .values_list('item_name', flat=True)
        .distinct()
    )

    totals['dinner_items'] = ", ".join(
        all_items.filter(meal_type='Dinner')
        .values_list('item_name', flat=True)
        .distinct()
    )

    grand_total = totals['total_sales']

    return render(request, 'sales/history.html', {
        'sales': sales.order_by('-date'),
        'totals': totals,
        'grand_total': grand_total,
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import DeliveryPlatform
from .forms import DeliveryPlatformForm


@admin_or_manager_required
def delivery_platform_list(request):
    query = request.GET.get('q', '')  # get search query from URL
    if query:
        platforms = DeliveryPlatform.objects.filter(name__icontains=query).order_by('name')
    else:
        platforms = DeliveryPlatform.objects.all().order_by('name')

    return render(request, 'sales/delivery_platform_list.html', {
        'platforms': platforms,
        'page_title': 'Manage Delivery Platforms',
        'search_query': query,  # pass current query to template
    })


@admin_or_manager_required
def add_delivery_platform(request):
    form = DeliveryPlatformForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Delivery Platform Added Successfully ✅")
            return redirect('delivery_platform_list')

    return render(request, 'sales/add_delivery_platform.html', {
        'form': form,
        'page_title': 'Add Delivery Platform'
    })


@admin_or_manager_required
def edit_delivery_platform(request, pk):
    platform = get_object_or_404(DeliveryPlatform, pk=pk)
    form = DeliveryPlatformForm(request.POST or None, instance=platform)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Delivery Platform Updated Successfully ✏️")
            return redirect('delivery_platform_list')

    return render(request, 'sales/add_delivery_platform.html', {
        'form': form,
        'page_title': 'Edit Delivery Platform'
    })


@admin_or_manager_required
def delete_delivery_platform(request, pk):
    platform = get_object_or_404(DeliveryPlatform, pk=pk)

    if request.method == "POST":
        platform.delete()
        messages.success(request, "Delivery Platform Deleted Successfully 🗑️")
        return redirect('delivery_platform_list')

    return render(request, 'sales/delivery_platform_delete.html', {
        'platform': platform,
        'page_title': 'Delete Delivery Platform'
    })



from datetime import datetime
from django.db.models import Q

@admin_or_manager_required
def cashbook_dashboard(request):

    selected_date = request.GET.get('date')
    user = request.user

    # Base queryset
    if user.user_type == 0:  # Admin
        cashbooks = CashBook.objects.all()
    else:  # Manager
        cashbooks = CashBook.objects.filter(branch=user.branch)

    # 🔎 Filter by date if selected
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            cashbooks = cashbooks.filter(date=selected_date)
        except ValueError:
            pass

    # ✅ Always show latest date first
    cashbooks = cashbooks.order_by('-date')

    return render(request, "cashbook/dashboard.html", {
        "cashbooks": cashbooks,
        "selected_date": selected_date
    })




@login_required
def toggle_day(request, branch_id, date):
    cash = get_object_or_404(CashBook, branch_id=branch_id, date=date)

    # Toggle the is_closed flag
    cash.is_closed = not cash.is_closed
    cash.save()

    status = "closed" if cash.is_closed else "reopened"
    messages.info(request, f"Day {status} successfully ✅")

    # Redirect back to your dashboard
    return redirect('cashbook_dashboard')  # replace with your actual page





from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db import transaction
from django.http import JsonResponse
import calendar
from .models import Salary,SalaryAdvance
from django.db.models.functions import Coalesce
from django.db.models import F, Sum,DecimalField, Value
from decimal import Decimal

# @login_required
# def add_salary(request):
#     staffs = Staff.objects.filter(branch=request.user.branch)
#     current_year = datetime.now().year
#     years = list(range(current_year - 5, current_year + 3))

#     if request.method == "POST":

#         staff_id = request.POST.get('staff')
#         salary_amount = Decimal(request.POST.get('salary_amount') or 0)
#         paid_amount = Decimal(request.POST.get('paid_amount') or 0)
#         next_month_advance = Decimal(request.POST.get('next_month_advance') or 0)

#         payment_date = request.POST.get('payment_date')
#         payment_mode = request.POST.get('payment_mode')

#         salary_month = request.POST.get('salary_month')
#         salary_year = int(request.POST.get('salary_year'))

#         staff = get_object_or_404(
#             Staff,
#             id=staff_id,
#             branch=request.user.branch
#         )

#         # Prevent duplicate salary
#         if Salary.objects.filter(
#             staff=staff,
#             salary_month=salary_month,
#             salary_year=salary_year
#         ).exists():
#             messages.info(request, "Salary already processed for this month.")
#             return redirect('salary_list')

#         # ==============================
#         # GET PREVIOUS SALARY RECORD
#         # ==============================
#         previous_salary = Salary.objects.filter(
#             staff=staff
#         ).filter(
#             Q(salary_year__lt=salary_year) |
#             Q(salary_year=salary_year, salary_month__lt=salary_month)
#         ).order_by('-salary_year', '-salary_month').first()

#         previous_balance = (
#             previous_salary.balance_salary
#             if previous_salary and previous_salary.balance_salary
#             else Decimal('0')
#         )

#         previous_next_month_advance = (
#             previous_salary.next_month_advance_amount
#             if previous_salary and previous_salary.next_month_advance_amount
#             else Decimal('0')
#         )

#         # ==============================
#         # FINAL BALANCE CALCULATION
#         # ==============================
#         balance_salary = (
#             salary_amount
#             + previous_balance
#             - paid_amount
#             - previous_next_month_advance
#         )

#         if balance_salary < 0:
#             balance_salary = Decimal('0')

#         # ==============================
#         # NEXT MONTH AUTO CALCULATION
#         # ==============================
#         month_list = [m[0] for m in Salary.MONTH_CHOICES]

#         if salary_month in month_list:
#             index = month_list.index(salary_month)

#             if index == 11:
#                 next_month = month_list[0]
#                 next_month_year = salary_year + 1
#             else:
#                 next_month = month_list[index + 1]
#                 next_month_year = salary_year
#         else:
#             next_month = None
#             next_month_year = None

#         # ==============================
#         # SAVE
#         # ==============================
#         with transaction.atomic():
#             Salary.objects.create(
#                 staff=staff,
#                 branch=request.user.branch,
#                 salary_amount=salary_amount,
#                 paid_amount=paid_amount,
#                 balance_salary=balance_salary,
#                 next_month_advance_amount=next_month_advance,
#                 salary_month=salary_month,
#                 salary_year=salary_year,
#                 next_month=next_month,
#                 next_month_year=next_month_year,
#                 payment_date=payment_date,
#                 payment_mode=payment_mode,
#                 created_by=request.user
#             )

#         messages.success(request, "Salary Processed Successfully ✅")
#         return redirect('salary_list')

#     return render(request, 'Manager/salary_add.html', {
#         'staffs': staffs,
#         'month_choices': Salary.MONTH_CHOICES,
#         'years': years,
#         'current_year': current_year,
#     })
from decimal import Decimal
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

@login_required
def add_salary(request):
    # staffs = Staff.objects.all()
    if request.user.branch_id:
        staffs = Staff.objects.filter(
             branch_id=request.user.branch_id
         )
    else:
         staffs = Staff.objects.none()
    month_choices = Salary.MONTH_CHOICES
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 3))

    if request.method == "POST":
        staff_id = request.POST.get('staff')
        salary_month = request.POST.get('salary_month')
        salary_year = int(request.POST.get('salary_year') or current_year)
        salary_amount = Decimal(request.POST.get('salary_amount') or 0)
        paid_amount = Decimal(request.POST.get('paid_amount') or 0)
        adjusted_advance = Decimal(request.POST.get('salary_advance') or 0)
        next_month_advance_amount = Decimal(request.POST.get('next_month_advance') or 0)
        payment_mode = request.POST.get('payment_mode')
        payment_date = request.POST.get('payment_date')

        if not staff_id or not salary_month or not salary_year:
            messages.error(request, "All fields are required.")
            return redirect('salary_list')

        staff = get_object_or_404(Staff, id=staff_id)

        # Prevent duplicate salary
        if Salary.objects.filter(staff=staff, salary_month=salary_month, salary_year=salary_year).exists():
            messages.error(request, "Salary already added for this month.")
            return redirect('salary_list')

        # Find previous month
        month_list = [m[0] for m in Salary.MONTH_CHOICES]
        index = month_list.index(salary_month)
        prev_month = month_list[11] if index == 0 else month_list[index - 1]
        prev_year = salary_year - 1 if index == 0 else salary_year

        # Get previous row
        previous_row = Salary.objects.filter(
            staff=staff,
            salary_month=prev_month,
            salary_year=prev_year
        ).order_by('-id').first()

        previous_balance = previous_row.balance_salary if previous_row else Decimal('0')
        advance_token = previous_row.next_month_advance_amount if previous_row and previous_row.next_month_advance_amount else Decimal('0')

        # FINAL BALANCE: current salary + previous balance - paid - advance
        balance_salary = salary_amount + previous_balance - paid_amount - advance_token
        if balance_salary < 0:
            balance_salary = Decimal('0')

        # Save
        Salary.objects.create(
            staff=staff,
            salary_amount=salary_amount,
            adjusted_advance=adjusted_advance,
            paid_amount=paid_amount,
            balance_salary=balance_salary,
            salary_month=salary_month,
            salary_year=salary_year,
            payment_mode=payment_mode,
            payment_date=payment_date,
            next_month_advance_amount=next_month_advance_amount,
            created_by=request.user
        )

        messages.success(request, f"Salary Added Successfully. Final Balance: {balance_salary}")
        return redirect('salary_list')

    return render(request, "Manager/salary_add.html", {
        'staffs': staffs,
        'years': years,
        'month_choices': month_choices,
        'current_year': current_year,
    })


@login_required
def get_previous_salary_data(request):
    staff_id = request.GET.get("staff_id")
    salary_month = request.GET.get("salary_month")
    salary_year = request.GET.get("salary_year")
    salary_amount = Decimal(request.GET.get("salary_amount") or 0)
    paid_amount = Decimal(request.GET.get("paid_amount") or 0)

    # Default values
    data = {
        "previous_month_salary": "0.00",
        "advance_token": "0.00",
        "previous_balance": "0.00",  # new
        "balance_preview": str(salary_amount)
    }

    if not staff_id or not salary_month or not salary_year:
        return JsonResponse(data)

    salary_year = int(salary_year)
    month_list = [m[0] for m in Salary.MONTH_CHOICES]
    index = month_list.index(salary_month)

    prev_month = month_list[11] if index == 0 else month_list[index - 1]
    prev_year = salary_year - 1 if index == 0 else salary_year

    previous_row = Salary.objects.filter(
        staff_id=staff_id,
        salary_month=prev_month,
        salary_year=prev_year
    ).order_by("-id").first()

    previous_month_salary = previous_row.salary_amount if previous_row else Decimal('0')
    advance_token = previous_row.next_month_advance_amount if previous_row and previous_row.next_month_advance_amount else Decimal('0')
    previous_balance = previous_row.balance_salary if previous_row else Decimal('0')  # new

    # New balance calculation: add previous balance
    balance_preview = salary_amount + previous_month_salary + previous_balance - paid_amount - advance_token
    if balance_preview < 0:
        balance_preview = Decimal('0')

    data.update({
        "previous_month_salary": str(previous_month_salary),
        "advance_token": str(advance_token),
        "previous_balance": str(previous_balance),
        "balance_preview": str(balance_preview)
    })

    return JsonResponse(data)


@login_required
def salary_list(request):

    salaries = Salary.objects.filter(
        staff__branch=request.user.branch
    ).select_related("staff", "branch")

    staff_name = request.GET.get("staff")
    selected_date = request.GET.get("date")
    selected_month = request.GET.get("month")

    # Staff filter
    if staff_name:
        salaries = salaries.filter(staff__name__icontains=staff_name)

    # Date filter
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            salaries = salaries.filter(payment_date=date_obj)
        except ValueError:
            selected_date = None

    # Month filter (YYYY-MM)
    if selected_month:
        try:
            year, month = selected_month.split("-")
            year = int(year)
            month = int(month)

            month_name = calendar.month_name[month]   # February, March etc

            salaries = salaries.filter(
                salary_year=year,
                salary_month=month_name
            )

        except Exception:
            selected_month = None


   

    salaries = salaries.order_by("-salary_year", "-salary_month", "-id")
    # ✅ TOTAL ONLY PAID AMOUNT
    total_paid = salaries.aggregate(
    total=Coalesce(
        Sum("paid_amount"),
        Value(0),
        output_field=DecimalField()
    )
    )["total"]


    context = {
        "salaries": salaries,
        "total_paid": total_paid,
        "staff_name": staff_name,
        "selected_date": selected_date,
        "selected_month": selected_month,
        "today_date": timezone.now().date(),
        "current_month": timezone.now().strftime("%Y-%m"),
    }

    return render(request, "Manager/salary_list.html", context)



@login_required
def edit_salary(request, pk):

    if request.user.user_type == 0:
        salary = get_object_or_404(Salary, pk=pk)
        staffs = Staff.objects.all()
    else:
        salary = get_object_or_404(
            Salary,
            pk=pk,
            branch=request.user.branch
        )
        staffs = Staff.objects.filter(branch=request.user.branch)

    # ✅ get total advance correctly
    total_advance = salary.adjusted_advance or Decimal('0')

    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 3))

    if request.method == "POST":

        salary_amount = Decimal(request.POST.get('salary_amount') or 0)

        adjusted_advance = Decimal(request.POST.get('salary_advance') or 0)

        pay_now = Decimal(request.POST.get('paid_amount') or 0)

        next_month_advance = Decimal(request.POST.get('next_month_advance') or 0)

        payment_date = request.POST.get('payment_date')
        payment_mode = request.POST.get('payment_mode')

        # total paid
        total_paid = (salary.paid_amount or Decimal('0')) + pay_now

        # balance
          # ✅ Balance using your formula
        balance_salary = salary_amount - total_paid

        salary.salary_amount = salary_amount
        salary.adjusted_advance = adjusted_advance
        salary.paid_amount = total_paid
        salary.balance_salary = balance_salary
        salary.next_month_advance_amount = next_month_advance
        salary.payment_date = payment_date
        salary.payment_mode = payment_mode

        salary.save()

        messages.success(request, "Salary updated successfully")
        return redirect('salary_list')

    return render(request, 'Manager/salary_edit.html', {
        'salary': salary,
        'staffs': staffs,
        'total_advance': total_advance,  # ✅ IMPORTANT
        'month_choices': Salary.MONTH_CHOICES,
        'years': years,
    })


@login_required
def delete_salary(request, pk):

    salary = get_object_or_404(
        Salary,
        pk=pk,
        staff__branch=request.user.branch
    )

    salary.delete()

    messages.success(request, "Salary deleted successfully.")
    return redirect('salary_list')

@login_required
def daily_salary_report(request):

    salaries = Salary.objects.filter(
        branch=request.user.branch,
        staff__salary_type="Daily"
    ).select_related('staff', 'branch')

    selected_date = request.GET.get("date")
    staff_name = request.GET.get("staff", "")

    # ✅ Apply date filter ONLY if user selects date
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            salaries = salaries.filter(payment_date=date_obj)
        except ValueError:
            pass

    # Staff filter
    if staff_name:
        salaries = salaries.filter(staff__name__icontains=staff_name)

    total_paid = salaries.aggregate(
        total=Sum("paid_amount")
    )["total"] or 0

    total_advance = salaries.aggregate(
        total=Sum("adjusted_advance")
    )["total"] or 0

    context = {
        "salaries": salaries,
        "total_paid": total_paid,
        "total_advance": total_advance,
        "selected_date": selected_date,
        "staff_name": staff_name,
        "today_date": date.today().strftime("%Y-%m-%d"),
    }

    return render(request, "Manager/daily_salaryreport.html", context)




@login_required
def monthly_salary_report(request):

    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    staff_name = request.GET.get('staff', '')

    user_branch = request.user.branch

    # ✅ Base Query:
    # Branch + Only Monthly Staff
    salaries = Salary.objects.filter(
        branch=user_branch,
        staff__salary_type="Monthly"
    )

    # ✅ Month filter
    if month:
        salaries = salaries.filter(salary_month__iexact=month)

    # ✅ Year filter
    if year:
        salaries = salaries.filter(salary_year=year)

    # ✅ Staff name filter
    if staff_name:
        salaries = salaries.filter(staff__name__icontains=staff_name)

    total_paid = salaries.aggregate(
        total=Sum('paid_amount')
    )['total'] or 0
    total_advance = salaries.aggregate(total=Sum('adjusted_advance'))['total'] or 0

    # Next Month Advance
    total_next_advance = salaries.aggregate(total=Sum('next_month_advance_amount'))['total'] or 0


    context = {
        'salaries': salaries.order_by('-id'),
        'total_paid': total_paid,
        'total_advance': total_advance,
        'total_next_advance': total_next_advance,
        'selected_month': month,
        'selected_year': year,
        'staff_name': staff_name,
    }

    return render(request, "Manager/monthly_salaryreport.html", context)


@login_required
def adminsalary_list(request):

    salaries = Salary.objects.select_related('staff', 'branch').all()

    staff_name = request.GET.get('staff', '').strip()
    selected_date = request.GET.get('date', '').strip()
    selected_branch = request.GET.get('branch', '').strip()
    selected_month = request.GET.get('month', '').strip()

    # 🔹 Restrict branch only if admin=0 AND no branch filter selected
    if hasattr(request.user, "admin") and request.user.admin == 0:
        if not selected_branch:
            salaries = salaries.filter(staff__branch=request.user.branch)

    # 🔹 Filter by staff name
    if staff_name:
        salaries = salaries.filter(staff__name__icontains=staff_name)

    # 🔹 Filter by branch
    if selected_branch and selected_branch.isdigit():
        salaries = salaries.filter(staff__branch_id=int(selected_branch))

    # 🔹 Filter by date
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            salaries = salaries.filter(payment_date=date_obj)
        except ValueError:
            pass

    if selected_month:
        salaries = salaries.filter(salary_month=selected_month)

    salaries = salaries.order_by("-salary_year", "-payment_date", "-id")

    total_paid = salaries.aggregate(
        total=Sum('paid_amount')
    )['total'] or 0

    branches = Branch.objects.all()
    month_choices = Salary.MONTH_CHOICES 

    context = {
        "salaries": salaries,
        "total_paid": total_paid,
        "branches": branches,
        "staff_name": staff_name,
        "selected_date": selected_date,
        "selected_branch": selected_branch,
        "month_choices": month_choices,      # send months
        "selected_month": selected_month,
    }

    return render(request, "Admin/salary_list.html", context)


def admindailysalary_list(request):

    salaries = Salary.objects.filter(
        staff__salary_type="Daily"
    ).select_related('staff', 'branch')

    selected_date = request.GET.get("date", "")
    staff_name = request.GET.get("staff", "")
    selected_branch = request.GET.get("branch", "")

    # DATE FILTER (ONLY IF SELECTED)
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            salaries = salaries.filter(payment_date=date_obj)
        except ValueError:
            pass

    # STAFF FILTER
    if staff_name:
        salaries = salaries.filter(staff__name__icontains=staff_name)

    # BRANCH FILTER
    if selected_branch and selected_branch.isdigit():
        salaries = salaries.filter(branch_id=int(selected_branch))

    # TOTALS
    total_paid = sum(s.paid_amount for s in salaries)
    total_advance = sum(s.adjusted_advance for s in salaries)

    branches = Branch.objects.all()

    context = {
        "salaries": salaries,
        "total_paid": total_paid,
        "total_advance": total_advance,
        "selected_date": selected_date,
        "staff_name": staff_name,
        "selected_branch": selected_branch,
        "branches": branches,
    }

    return render(request, 'Admin/admindaily_salaryreport.html', context)



from django.shortcuts import render
from django.db.models import Sum

def adminmonthly_salary_report(request):
    """
    Show monthly salary report for all branches by default.
    Filters are optional. Default shows all branches.
    """
    # Get optional filters
    staff_name = request.GET.get('staff', '').strip()
    month = request.GET.get('month', '').strip()  # e.g., "February"
    year = request.GET.get('year', '').strip()    # e.g., "2026"
    branch_id = request.GET.get('branch', '').strip()


# )
    salaries = Salary.objects.select_related('staff', 'branch').filter(
    staff__salary_type="Monthly"  # Include all Monthly staff
)




    # Apply optional filters
    if staff_name:
        salaries = salaries.filter(staff__name__icontains=staff_name)

    if month:
        salaries = salaries.filter(salary_month__iexact=month)

    if year:
        try:
            salaries = salaries.filter(salary_year=int(year))
        except ValueError:
            pass

    
    if branch_id and branch_id.isdigit():
        salaries = salaries.filter(branch_id=int(branch_id))

    # Aggregate totals
    totals = salaries.aggregate(
        total_paid=Sum('paid_amount'),
        total_advance=Sum('adjusted_advance'),
        total_next_advance=Sum('next_month_advance_amount'),
        total_balance=Sum('balance_salary'),
    )

    # For template filters
    branches = Branch.objects.all()
    month_list = [m[0] for m in Salary.MONTH_CHOICES]

    context = {
        'salaries': salaries.order_by('-salary_year', '-salary_month'),
        'branches': branches,
        'month_list': month_list,
        'total_paid': totals['total_paid'] or 0,
        'total_advance': totals['total_advance'] or 0,
        'total_next_advance': totals['total_next_advance'] or 0,
        'total_balance': totals['total_balance'] or 0,
        'staff_name': staff_name,
        'selected_month': month,
        'selected_year': year,
        'selected_branch': branch_id,
    }


    return render(request, 'Admin/adminmontly_salaryreport.html', context)

@login_required
def admin_add_staff(request):
    # Get all managers
    managers = Manager.objects.select_related('user').all()

    if request.method == "POST":
        staff_id = request.POST.get("staff_id").strip()
        name = request.POST.get("name").strip()
        gender = request.POST.get("gender")
        role = request.POST.get("role")
        contact = request.POST.get("contact").strip()
        dob = request.POST.get("dob") or None
        joining_date = request.POST.get("joining_date")
        salary_type = request.POST.get("salary_type")
        status = request.POST.get("status")
        manager_id = request.POST.get("manager")

        # Get selected manager
        manager = Manager.objects.filter(id=manager_id).first() if manager_id else None

        if not manager:
            messages.error(request, "Please select a valid manager.")
            return redirect("admin_add_staff")

        # Staff branch = manager's branch
        branch = manager.user.branch

        # Check duplicate staff_id
        if Staff.objects.filter(staff_id=staff_id).exists():
            messages.error(request, f"Staff ID {staff_id} already exists!")
            return redirect("admin_add_staff")

        # Save staff
        Staff.objects.create(
            staff_id=staff_id,
            name=name,
            gender=gender,
            role=role,
            contact=contact,
            dob=dob,
            joining_date=joining_date,
            salary_type=salary_type,
            status=status,
            branch=branch,
            created_by=request.user
        )

        messages.success(request, f"Staff '{name}' added successfully ✅")
        # return redirect("admin_add_staff")
        return redirect("adminview_staff")
  # Make sure this URL exists

    return render(request, "Admin/adminstaff_add.html", {
        "managers": managers
    })

@login_required
def admin_edit_staff(request, id):
    staff = get_object_or_404(Staff, id=id)
    managers = Manager.objects.select_related('user').all()

    if request.method == "POST":
        staff_id_input = request.POST.get("staff_id", "").strip()
        name = request.POST.get("name", "").strip()
        gender = request.POST.get("gender")
        role = request.POST.get("role")
        contact = request.POST.get("contact", "").strip()
        dob = request.POST.get("dob") or None
        joining_date = request.POST.get("joining_date")
        salary_type = request.POST.get("salary_type")
        status = request.POST.get("status")
        manager_id = request.POST.get("manager")

        # ✅ Duplicate check
        if Staff.objects.filter(staff_id=staff_id_input).exclude(id=staff.id).exists():
            messages.error(request, f"Staff ID {staff_id_input} already exists!")
            return redirect("edit_staff", id=staff.id)

        # ✅ Update basic fields
        staff.staff_id = staff_id_input
        staff.name = name
        staff.gender = gender
        staff.role = role
        staff.contact = contact
        staff.dob = dob
        staff.joining_date = joining_date
        staff.salary_type = salary_type
        staff.status = status

        # ✅ IMPORTANT: Update manager (created_by)
        if manager_id:
            manager = Manager.objects.filter(id=manager_id).first()
            if manager:
                staff.branch = manager.user.branch
                staff.created_by = manager.user   # ⭐ THIS LINE FIXES YOUR ISSUE
            else:
                messages.error(request, "Invalid manager selected.")
                return redirect("edit_staff", id=staff.id)

        staff.save()

        messages.success(request, f"Staff '{name}' updated successfully ✅")
        return redirect("adminview_staff")

    return render(request, "Admin/admin_edit_staff.html", {
        "staff": staff,
        "managers": managers
    })

   



def admindelete_staff(request, id):
    staff = get_object_or_404(Staff, id=id)

    staff.delete()

    messages.success(request, "Staff deleted successfully 🗑️")
    return redirect('adminview_staff')


from decimal import Decimal
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def adminadd_salary(request):
    staffs = Staff.objects.all()
    month_choices = Salary.MONTH_CHOICES
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 3))

    if request.method == "POST":
        staff_id = request.POST.get('staff')
        salary_month = request.POST.get('salary_month')
        salary_year = int(request.POST.get('salary_year') or current_year)
        salary_amount = Decimal(request.POST.get('salary_amount') or 0)
        paid_amount = Decimal(request.POST.get('paid_amount') or 0)
        adjusted_advance = Decimal(request.POST.get('salary_advance') or 0)
        next_month_advance_amount = Decimal(request.POST.get('next_month_advance') or 0)
        payment_mode = request.POST.get('payment_mode')
        payment_date = request.POST.get('payment_date')

        if not staff_id or not salary_month or not salary_year:
            messages.error(request, "All fields are required.")
            return redirect('admin_salary_list')

        staff = get_object_or_404(Staff, id=staff_id)

        # Prevent duplicate salary
        if Salary.objects.filter(staff=staff, salary_month=salary_month, salary_year=salary_year).exists():
            messages.error(request, "Salary already added for this month.")
            return redirect('admin_salary_list')

        # Find previous month
        month_list = [m[0] for m in Salary.MONTH_CHOICES]
        index = month_list.index(salary_month)
        prev_month = month_list[11] if index == 0 else month_list[index - 1]
        prev_year = salary_year - 1 if index == 0 else salary_year

        # Get previous row
        previous_row = Salary.objects.filter(
            staff=staff,
            salary_month=prev_month,
            salary_year=prev_year
        ).order_by('-id').first()

        previous_balance = previous_row.balance_salary if previous_row else Decimal('0')
        advance_token = previous_row.next_month_advance_amount if previous_row and previous_row.next_month_advance_amount else Decimal('0')

        # FINAL BALANCE: current salary + previous balance - paid - advance
        balance_salary = salary_amount + previous_balance - paid_amount - advance_token
        if balance_salary < 0:
            balance_salary = Decimal('0')

        # Save
        Salary.objects.create(
            staff=staff,
            salary_amount=salary_amount,
            adjusted_advance=adjusted_advance,
            paid_amount=paid_amount,
            balance_salary=balance_salary,
            salary_month=salary_month,
            salary_year=salary_year,
            payment_mode=payment_mode,
            payment_date=payment_date,
            next_month_advance_amount=next_month_advance_amount,
            created_by=request.user
        )

        messages.success(request, f"Salary Added Successfully. Final Balance: {balance_salary}")
        return redirect('admin_salary_list')

    return render(request, 'Admin/admin_add_salary.html', {
        'staffs': staffs,
        'years': years,
        'month_choices': month_choices,
        'current_year': current_year,
    })


@login_required
def get_previous_salary_data(request):
    staff_id = request.GET.get("staff_id")
    salary_month = request.GET.get("salary_month")
    salary_year = request.GET.get("salary_year")
    salary_amount = Decimal(request.GET.get("salary_amount") or 0)
    paid_amount = Decimal(request.GET.get("paid_amount") or 0)

    # Default values
    data = {
        "previous_month_salary": "0.00",
        "advance_token": "0.00",
        "previous_balance": "0.00",  # new
        "balance_preview": str(salary_amount)
    }

    if not staff_id or not salary_month or not salary_year:
        return JsonResponse(data)

    salary_year = int(salary_year)
    month_list = [m[0] for m in Salary.MONTH_CHOICES]
    index = month_list.index(salary_month)

    prev_month = month_list[11] if index == 0 else month_list[index - 1]
    prev_year = salary_year - 1 if index == 0 else salary_year

    previous_row = Salary.objects.filter(
        staff_id=staff_id,
        salary_month=prev_month,
        salary_year=prev_year
    ).order_by("-id").first()

    previous_month_salary = previous_row.salary_amount if previous_row else Decimal('0')
    advance_token = previous_row.next_month_advance_amount if previous_row and previous_row.next_month_advance_amount else Decimal('0')
    previous_balance = previous_row.balance_salary if previous_row else Decimal('0')  # new

    # New balance calculation: add previous balance
    balance_preview = salary_amount + previous_month_salary + previous_balance - paid_amount - advance_token
    if balance_preview < 0:
        balance_preview = Decimal('0')

    data.update({
        "previous_month_salary": str(previous_month_salary),
        "advance_token": str(advance_token),
        "previous_balance": str(previous_balance),
        "balance_preview": str(balance_preview)
    })

    return JsonResponse(data)

@login_required
def adminedit_salary(request, pk):

    if request.user.user_type == 0:
        salary = get_object_or_404(Salary, pk=pk)
        staffs = Staff.objects.all()
    else:
        salary = get_object_or_404(
            Salary,
            pk=pk,
            branch=request.user.branch
        )
        staffs = Staff.objects.filter(branch=request.user.branch)

    # ✅ get total advance correctly
    total_advance = salary.adjusted_advance or Decimal('0')

    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 3))

    if request.method == "POST":

        salary_amount = Decimal(request.POST.get('salary_amount') or 0)

        adjusted_advance = Decimal(request.POST.get('salary_advance') or 0)

        pay_now = Decimal(request.POST.get('paid_amount') or 0)

        next_month_advance = Decimal(request.POST.get('next_month_advance') or 0)

        payment_date = request.POST.get('payment_date')
        payment_mode = request.POST.get('payment_mode')

        # total paid
        total_paid = (salary.paid_amount or Decimal('0')) + pay_now

        # balance
          # ✅ Balance using your formula
        balance_salary = salary_amount - total_paid

        salary.salary_amount = salary_amount
        salary.adjusted_advance = adjusted_advance
        salary.paid_amount = total_paid
        salary.balance_salary = balance_salary
        salary.next_month_advance_amount = next_month_advance
        salary.payment_date = payment_date
        salary.payment_mode = payment_mode

        salary.save()

        messages.success(request, "Salary updated successfully")
        return redirect('admin_salary_list')

    return render(request, 'Admin/adminsalary_edit.html', {
        'salary': salary,
        'staffs': staffs,
        'total_advance': total_advance,  # ✅ IMPORTANT
        'month_choices': Salary.MONTH_CHOICES,
        'years': years,
    })


@login_required
def admindelete_salary(request, pk):

    # ✅ real admin (user_type = 0)
    if request.user.user_type == 0:
        # admin → can delete any salary
        salary = get_object_or_404(Salary, pk=pk)
    else:
        # others → only own branch
        salary = get_object_or_404(
            Salary,
            pk=pk,
            branch=request.user.branch
        )

    salary.delete()

    messages.success(request, "Salary deleted successfully.")

    return redirect('admin_salary_list')


# @login_required
# def manager_salary(request):

#     managers = Manager.objects.select_related("user")

#     if request.method == "POST":

#         manager_id   = request.POST.get("manager")
#         salary_month = request.POST.get("salary_month")
#         salary_year  = request.POST.get("salary_year")
#         balance        = request.POST.get("balance")  
#         salary_amount = Decimal(request.POST.get("salary_amount") or 0)
#         paid_amount   = Decimal(request.POST.get("paid_amount") or 0)
#         adjusted_advance = Decimal(request.POST.get("salary_advance") or 0)
#         next_month_advance = Decimal(request.POST.get("next_month_advance") or 0)

#         if not manager_id or not salary_month or not salary_year:
#             messages.error(request, "All fields are required.")
#             return redirect("manager_salary_list")

#         salary_year = int(salary_year)

#         # -----------------------------------------
#         # prevent duplicate manager salary
#         # -----------------------------------------
#         if ManagerSalary.objects.filter(
#             manager_id=manager_id,
#             salary_month=salary_month,
#             salary_year=salary_year
#         ).exists():
#             messages.error(request, "Salary already added for this month.")
#             return redirect("manager_salary_list")

#         # -----------------------------------------
#         # find previous month
#         # -----------------------------------------
#         month_list = [m[0] for m in ManagerSalary.MONTH_CHOICES]
#         index = month_list.index(salary_month)

#         if index == 0:
#             prev_month = month_list[11]
#             prev_year  = salary_year - 1
#         else:
#             prev_month = month_list[index - 1]
#             prev_year  = salary_year

#         # -----------------------------------------
#         # get previous salary row
#         # -----------------------------------------
#         previous_row = ManagerSalary.objects.filter(
#             manager_id=manager_id,
#             salary_month=prev_month,
#             salary_year=prev_year
#         ).order_by("-id").first()

#         previous_balance = Decimal("0")
#         previous_next_month_advance = Decimal("0")

#         if previous_row:
#             previous_balance = previous_row.balance_salary or Decimal("0")
#             previous_next_month_advance = (
#                 previous_row.next_month_advance_amount or Decimal("0")
#             )

#         # -----------------------------------------
#         # final balance calculation
#         # (same logic as staff salary)
#         # -----------------------------------------
#         balance_salary = salary_amount - (
#             paid_amount +
#             previous_balance +
#             previous_next_month_advance
#         )

#         if balance_salary < 0:
#             balance_salary = Decimal("0")

#         # -----------------------------------------
#         # save
#         # -----------------------------------------
#         ManagerSalary.objects.create(
#             manager_id=manager_id,
#             branch_id=request.POST.get("branch"),
#             salary_amount=salary_amount,
#             paid_amount=paid_amount,
#             adjusted_advance=adjusted_advance,
#             balance_salary=balance_salary,   # ✅ important
#             salary_month=salary_month,
#             salary_year=salary_year,
#             payment_date=request.POST.get("payment_date"),
#             payment_mode=request.POST.get("payment_mode"),
#             next_month_advance_amount=next_month_advance,
#             created_by=request.user,
            
#         )

#         messages.success(request, "Manager salary added successfully.")
#         return redirect("manager_salary_list")

#     context = {
#         "managers": managers,
#         "month_choices": ManagerSalary.MONTH_CHOICES,
#         "years": range(2022, 2035),
#         "current_year": datetime.now().year,
#     }

#     return render(request, "Admin/manager_salary.html", context)
@login_required
def manager_salary(request):

    managers = Manager.objects.select_related("user")

    if request.method == "POST":

        manager_id   = request.POST.get("manager")
        salary_month = request.POST.get("salary_month")
        salary_year  = request.POST.get("salary_year")

        salary_amount = Decimal(request.POST.get("salary_amount") or 0)
        paid_amount   = Decimal(request.POST.get("paid_amount") or 0)
        adjusted_advance = Decimal(request.POST.get("salary_advance") or 0)
        next_month_advance = Decimal(request.POST.get("next_month_advance") or 0)

        if not manager_id or not salary_month or not salary_year:
            messages.error(request, "All fields are required.")
            return redirect("manager_salary_list")

        salary_year = int(salary_year)

        # prevent duplicate
        if ManagerSalary.objects.filter(
            manager_id=manager_id,
            salary_month=salary_month,
            salary_year=salary_year
        ).exists():
            messages.error(request, "Salary already added for this month.")
            return redirect("manager_salary_list")

        # -------------------------
        # find previous month
        # -------------------------
        month_list = [m[0] for m in ManagerSalary.MONTH_CHOICES]
        index = month_list.index(salary_month)

        if index == 0:
            prev_month = month_list[11]
            prev_year  = salary_year - 1
        else:
            prev_month = month_list[index - 1]
            prev_year  = salary_year

        previous_row = ManagerSalary.objects.filter(
            manager_id=manager_id,
            salary_month=prev_month,
            salary_year=prev_year
        ).order_by("-id").first()

        previous_balance = Decimal("0")
        previous_next_month_advance = Decimal("0")

        if previous_row:
            previous_balance = previous_row.balance_salary or Decimal("0")
            previous_next_month_advance = (
                previous_row.next_month_advance_amount or Decimal("0")
            )

        # --------------------------------------------------
        # ✅ ONLY CORRECT BUSINESS FORMULA
        #
        # balance = salary - previous balance - previous advance - paid
        # --------------------------------------------------
        balance_salary = (
    salary_amount
    + previous_balance
    - previous_next_month_advance
    - paid_amount
)

        if balance_salary < 0:
            balance_salary = Decimal("0")

        ManagerSalary.objects.create(
            manager_id=manager_id,
            branch_id=request.POST.get("branch"),
            salary_amount=salary_amount,
            paid_amount=paid_amount,
            adjusted_advance=adjusted_advance,
            balance_salary=balance_salary,
            salary_month=salary_month,
            salary_year=salary_year,
            payment_date=request.POST.get("payment_date"),
            payment_mode=request.POST.get("payment_mode"),
            next_month_advance_amount=next_month_advance,
            created_by=request.user,
        )

        messages.success(request, "Manager salary added successfully.")
        return redirect("manager_salary_list")

    context = {
        "managers": managers,
        "month_choices": ManagerSalary.MONTH_CHOICES,
        "years": range(2022, 2035),
        "current_year": datetime.now().year,
    }

    return render(request, "Admin/manager_salary.html", context)

def get_previous_manager_salary_data(request):

    manager_id   = request.GET.get("manager_id")
    salary_month = request.GET.get("salary_month")
    salary_year  = request.GET.get("salary_year")

    data = {
        "previous_balance": "0.00",
        "previous_next_month_advance": "0.00",
    }

    if not manager_id or not salary_month or not salary_year:
        return JsonResponse(data)

    salary_year = int(salary_year)

    month_list = [m[0] for m in ManagerSalary.MONTH_CHOICES]
    index = month_list.index(salary_month)

    if index == 0:
        prev_month = month_list[11]
        prev_year = salary_year - 1
    else:
        prev_month = month_list[index - 1]
        prev_year = salary_year

    previous_row = ManagerSalary.objects.filter(
        manager_id=manager_id,
        salary_month=prev_month,
        salary_year=prev_year
    ).order_by("-id").first()

    if previous_row:
        data["previous_balance"] = str(previous_row.balance_salary or 0)
        data["previous_next_month_advance"] = str(
            previous_row.next_month_advance_amount or 0
        )

    return JsonResponse(data)

@login_required
def manager_salary_list(request):

    salaries = ManagerSalary.objects.select_related(
        "manager__user__branch",
        "branch"
    ).order_by("-salary_year", "-salary_month")

    # Get Filters
    manager = request.GET.get("manager")
    month = request.GET.get("month")
    year = request.GET.get("year")
    branch = request.GET.get("branch")   # ✅ Added

    # Apply Filters
    if branch:
        salaries = salaries.filter(branch_id=branch)

    if manager:
        salaries = salaries.filter(manager_id=manager)

    if month:
        salaries = salaries.filter(salary_month=month)

    if year:
        salaries = salaries.filter(salary_year=year)

    # Calculate total dynamically AFTER filtering
    total_paid = salaries.aggregate(
        total=Sum("paid_amount")
    )["total"] or Decimal("0.00")

    context = {
        "salaries": salaries,
        "total_paid": total_paid,
        "managers": Manager.objects.all(),
        "branches": Branch.objects.all(),   # ✅ Pass branches
        "month_choices": ManagerSalary.MONTH_CHOICES,
        "years": range(2022, 2031),
    }

    return render(request, "Admin/managersalary_list.html", context)


@login_required
def manager_salary_edit(request, pk):
    salary = get_object_or_404(ManagerSalary, pk=pk)

    managers = Manager.objects.all()
    branches = Branch.objects.all()
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 5))

    if request.method == "POST":

        salary.manager_id = request.POST.get("manager")
        salary.branch_id = request.POST.get("branch")
        salary.salary_month = request.POST.get("salary_month")
        salary.salary_year = int(request.POST.get("salary_year") or 0)

        salary_amount = salary.salary_amount
        advance = Decimal(request.POST.get("salary_advance") or 0)

        # ✅ Use DB value for already paid
        already_paid = salary.paid_amount
        pay_now = Decimal(request.POST.get("pay_now") or 0)

        # Total paid = previous + new
        total_paid = already_paid + pay_now

        # Calculate balance correctly
        balance = salary_amount - advance - total_paid
        if balance < 0:
            balance = Decimal("0.00")

        # Update DB fields
        salary.adjusted_advance = advance
        salary.paid_amount = total_paid
        salary.balance_salary = balance
        

        salary.payment_mode = request.POST.get("payment_mode")
        salary.payment_date = request.POST.get("payment_date")

        salary.next_month_advance_amount = Decimal(request.POST.get("next_month_advance") or 0)
        salary.next_month = request.POST.get("next_month") or None
        next_year = request.POST.get("next_month_year")
        salary.next_month_year = int(next_year) if next_year else None

        salary.save()
        messages.success(request, "Manager salary updated successfully")
        return redirect("manager_salary_list")

    context = {
        "salary": salary,
        "managers": managers,
        "branches": branches,
        "month_choices": ManagerSalary.MONTH_CHOICES,
        "years": years,
        "current_year": current_year,
    }

    return render(request, "Admin/managersalary_edit.html", context)



@login_required
def managerdelete_salary(request, pk):


    salary = get_object_or_404(ManagerSalary, pk=pk)

    salary.delete()

    messages.success(request, "Manager salary deleted successfully")

    return redirect("manager_salary_list")



@login_required
def manager_monthly_report(request):

    salaries = ManagerSalary.objects.select_related(
        "manager__user__branch",
        "branch"
    ).order_by("-salary_year", "-salary_month")

    manager = request.GET.get("manager")
    month = request.GET.get("month")
    year = request.GET.get("year")
    branch = request.GET.get("branch")

    if manager and manager != "":
        salaries = salaries.filter(manager_id=int(manager))

    if month and month != "":
        salaries = salaries.filter(salary_month=month)

    if year and year != "":
        salaries = salaries.filter(salary_year=int(year))

    if branch and branch != "":
        salaries = salaries.filter(branch_id=int(branch))

    total_paid = salaries.aggregate(
        total=Sum("paid_amount")
    )["total"] or Decimal("0.00")

    context = {
        "salaries": salaries,
        "total_paid": total_paid,
        "managers": Manager.objects.all(),
        "branches": Branch.objects.all(),
        "month_choices": ManagerSalary.MONTH_CHOICES,
        "years": range(2022, 2031),
    }


    return render(
        request,
        'Admin/adminmontly_salaryreport.html',
        context
    )
    
    
    
from django.db.models import Sum, Count
from datetime import datetime
from .models import DeliverySale

from datetime import datetime
from django.db.models import Q, Sum, Count
from datetime import datetime

@admin_or_manager_required


def delivery_performance_report(request):
    user = request.user

    order_id = request.GET.get('order_id')
    staff_id = request.GET.get('staff')
    selected_date = request.GET.get('date')

    # Staff visibility
    if user.user_type == 0:
        staff_list = Staff.objects.filter(role='Delivery', status='Active')
    else:
        staff_list = Staff.objects.filter(
            role='Delivery',
            status='Active'
        ).filter(
            Q(branch=user.branch) |
            Q(created_by__user_type=0) |
            Q(created_by=user)
        ).distinct()

    deliveries = DeliverySale.objects.select_related(
        'staff', 'sale'
    ).filter(staff__in=staff_list)

    # Filters
    if order_id:
        deliveries = deliveries.filter(order_id__icontains=order_id)

    if staff_id:
        deliveries = deliveries.filter(staff__id=staff_id)

    if selected_date:
        try:
            filter_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            deliveries = deliveries.filter(sale__date=filter_date)
        except ValueError:
            pass

    # Performance
    performance = deliveries.values(
        'staff__id',
        'staff__name'
    ).annotate(
        total_amount=Sum('amount'),
        total_orders=Count('id')
    ).order_by('-total_amount')

    grand_total = deliveries.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'sales/delivery_report.html', {
        'performance': performance,
        'deliveries': deliveries,
        'grand_total': grand_total,
        'staff_list': staff_list,
        'selected_date': selected_date,
    })



    
    
    
from django.shortcuts import render, redirect
from .models import CommunicationSettings
from .forms import CommunicationSettingsForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import CommunicationSettings
from .forms import CommunicationSettingsForm


# ================= LIST PAGE =================
def communication_settings_list(request):
    settings = CommunicationSettings.objects.all()
    return render(request, 'Admin/communication_settings_list.html', {
        'settings': settings
    })


# ================= ADD =================
def communication_settings_add(request):
    if request.method == 'POST':
        form = CommunicationSettingsForm(request.POST)
        if form.is_valid():
            config = form.save()

            if config.is_active:
                   CommunicationSettings.objects.exclude(id=config.id).update(is_active=False)
            messages.success(request, "Settings added successfully")
            return redirect('communication_settings_list')
    else:
        form = CommunicationSettingsForm()

    return render(request, 'Admin/communication_settings_form.html', {
        'form': form,
        'title': 'Add Communication Settings'
    })


# ================= EDIT =================
def communication_settings_edit(request, pk):
    config = get_object_or_404(CommunicationSettings, pk=pk)

    if request.method == 'POST':
        form = CommunicationSettingsForm(request.POST, instance=config)
        if form.is_valid():
            config = form.save()

            if config.is_active:
                
                CommunicationSettings.objects.exclude(id=config.id).update(is_active=False)
            messages.success(request, "Settings updated successfully")
            return redirect('communication_settings_list')
    else:
        form = CommunicationSettingsForm(instance=config)

    return render(request, 'Admin/communication_settings_form.html', {
        'form': form,
        'title': 'Edit Communication Settings'
    })


# ================= DELETE =================
def communication_settings_delete(request, pk):
    config = get_object_or_404(CommunicationSettings, pk=pk)
    config.delete()
    messages.success(request, "Settings deleted successfully")
    return redirect('communication_settings_list')

def reports_list(request):
    reports = [
        {"name": "Delivery Performance", "url": "delivery_report"},
        {"name": "Sales History", "url": "history_sales"},
        {"name": "Expense History", "url": "history_expenses"},
    ]
    return render(request, "reports/reports_list.html", {"reports": reports})
def export_report_page(request, report_type):
    query_params = request.GET.urlencode()

    if report_type == "expense":
        action_url = reverse('send_expense_report')
    elif report_type == "delivery":
        action_url = reverse('send_report', args=['delivery'])
    elif report_type == "sales":
        action_url = reverse('send_sales_report')

    return render(request, "reports/export_page.html", {
        'report_type': report_type,
        'query_params': query_params,
        'action_url': action_url
    })
from django.shortcuts import render, redirect
from django.db.models import Sum, Count
from datetime import datetime
from .models import DeliverySale, Staff
from .utils import generate_pdf, save_pdf_and_get_link, send_email_report, send_whatsapp, send_whatsapp_report


from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from datetime import datetime
from django.db.models import Sum, Count


from datetime import datetime
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum, Count
from django.core.exceptions import ValidationError

from .models import Staff, DeliverySale
from .utils import generate_pdf, send_email_report, save_pdf_and_get_link, send_whatsapp
from .validators import phone_validator


def send_report(request, report_type):
    user = request.user

    # Keep filters
    query_params = request.GET.urlencode()

    # ===== Get filters =====
    order_id = request.GET.get('order_id')
    staff_id = request.GET.get('staff')
    selected_date = request.GET.get('date')

    # ===== Staff visibility =====
    if user.user_type == 0:
        staff_list = Staff.objects.filter(role='Delivery', status='Active')
    else:
        staff_list = Staff.objects.filter(
            role='Delivery',
            status='Active',
            branch=user.branch
        )

    deliveries = DeliverySale.objects.select_related('staff', 'sale').filter(
        staff__in=staff_list
    )

    # ===== Apply Filters =====
    if order_id:
        deliveries = deliveries.filter(order_id__icontains=order_id)

    if staff_id:
        deliveries = deliveries.filter(staff__id=staff_id)

    if selected_date:
        try:
            filter_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            deliveries = deliveries.filter(sale__date=filter_date)
        except ValueError:
            pass

    # ===== Summary =====
    performance = deliveries.values(
        'staff__name'
    ).annotate(
        total_amount=Sum('amount'),
        total_orders=Count('id')
    )

    grand_total = deliveries.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'deliveries': deliveries,
        'performance': performance,
        'grand_total': grand_total,
        'selected_date': selected_date,
    }

    # ===== Generate PDF =====
    pdf = generate_pdf("sales/delivery_report_export.html", context)

    # ===== Send Action =====
    if request.method == "POST":
        send_via = request.POST.get("send_via")
        email = (request.POST.get("email") or "").strip()
        number = (request.POST.get("whatsapp") or "").strip()

        # ===== Email Validation =====
        if send_via == "email":
            if not email:
                messages.info(request, "Please enter Email to send the report.")
                return redirect(f"{reverse('export_report_page', args=[report_type])}?{query_params}")

            send_email_report(
                email,
                "Delivery Report",
                f"Delivery Total: {grand_total}",
                pdf
            )
            messages.success(request, "Report sent successfully via Email.")
            return redirect(f"{reverse('delivery_report')}?{query_params}")

        # ===== WhatsApp Validation =====
        elif send_via == "whatsapp":
            if not number:
                messages.info(request, "Please enter WhatsApp number.")
                return redirect(f"{reverse('export_report_page', args=[report_type])}?{query_params}")

            # Format validation
            try:
                phone_validator(number)
            except ValidationError as e:
                messages.error(request, e.message)
                return redirect(f"{reverse('export_report_page', args=[report_type])}?{query_params}")

            # Generate PDF link
            pdf_link = save_pdf_and_get_link(request, pdf)

            message = (
                f"Delivery Report Total: {grand_total}\n"
                f"Download PDF: {pdf_link}"
            )

            return send_whatsapp(number, message)

    # ===== Open Export Page =====
    return render(request, "reports/export_page.html", {
        'report_type': report_type,
        'query_params': query_params
    })



from django.db.models import Sum
from django.contrib import messages
from django.urls import reverse
from datetime import datetime
from .models import Expense, Branch
from .utils import generate_pdf, send_email_report, send_whatsapp, save_pdf_and_get_link

@admin_or_manager_required
def send_expense_report(request):
    report_type = "expense"
    user = request.user
    query_params = request.GET.urlencode()

    # ===== Filters =====
    start = request.GET.get('start')
    end = request.GET.get('end')
    month = request.GET.get('month')
    branch_name = request.GET.get('branch', '').strip()

    # ===== Base queryset =====
    if user.user_type == 0:
        expenses = Expense.objects.all()
    else:
        expenses = Expense.objects.filter(branch=user.branch)

    # Branch filter (admin only)
    if branch_name and user.user_type == 0:
        expenses = expenses.filter(branch__name__icontains=branch_name)

    # Date range
    if start and end:
        expenses = expenses.filter(date__range=[start, end])

    # Month filter
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            expenses = expenses.filter(date__year=year, date__month=month_num)
        except ValueError:
            pass

    # ===== Summary =====
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'expenses': expenses,
        'total': total,
        'start': start,
        'end': end,
        'month': month,
        'branch': branch_name,
    }

    # ===== Generate PDF =====
    pdf = generate_pdf("expenses/expense_report_export.html", context)

    # ===== Send Action =====
    if request.method == "POST":
        send_via = request.POST.get("send_via")
        email = (request.POST.get("email") or "").strip()
        number = (request.POST.get("whatsapp") or "").strip()

        # ===== Email Validation =====
        if send_via == "email":
            if not email:
                messages.info(request, "Please enter Email to send the report.")
                return redirect(f"{reverse('export_report_page', args=[report_type])}?{query_params}")

            send_email_report(
                email,
                "Expense Report",
                f"Total Expense: {total}",
                pdf
            )
            messages.success(request, "Expense report sent via Email.")
            return redirect(f"{reverse('history_expenses')}?{query_params}")

        # ===== WhatsApp Validation =====
        elif send_via == "whatsapp":
            if not number:
                messages.info(request, "Please enter WhatsApp number.")
                return redirect(f"{reverse('export_report_page', args=[report_type])}?{query_params}")

            # Format validation
            try:
                phone_validator(number)
            except ValidationError as e:
                messages.error(request, e.message)
                return redirect(f"{reverse('export_report_page', args=[report_type])}?{query_params}")

            # Generate PDF link
            pdf_link = save_pdf_and_get_link(request, pdf)

            message = (
                f"Expense Report Total: {total}\n"
                f"Download PDF: {pdf_link}"
            )

            return send_whatsapp(number, message)

    # ===== Open Export Page =====
    return render(request, "reports/export_page.html", {
        'report_type': report_type,
        'query_params': query_params
    })
from django.db.models import Sum
from django.contrib import messages
from django.urls import reverse
from datetime import datetime
from .models import DailySale, DailySaleItem
from .utils import generate_pdf, send_email_report, send_whatsapp, save_pdf_and_get_link


@admin_or_manager_required
def send_sales_report(request):
    report_type = "sales"
    user = request.user
    query_params = request.GET.urlencode()

    # ===== Filters =====
    start = request.GET.get('start')   # <-- missing earlier
    end = request.GET.get('end')
    month = request.GET.get('month')
    branch_name = request.GET.get('branch', '').strip()

    # ===== Base queryset =====
    if user.user_type == 0:
        sales = DailySale.objects.all()
    else:
        sales = DailySale.objects.filter(branch=user.branch)

    # Branch filter (admin)
    if branch_name and user.user_type == 0:
        sales = sales.filter(branch__name__icontains=branch_name)

    # Month filter (priority)
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            sales = sales.filter(date__year=year, date__month=month_num)
        except ValueError:
            pass

    # Date range
    elif start and end:
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            sales = sales.filter(date__range=[start_date, end_date])
        except ValueError:
            pass

    # ===== Totals =====
    totals = sales.aggregate(
        total_breakfast=Sum('breakfast_total'),
        total_lunch=Sum('lunch_total'),
        total_dinner=Sum('dinner_total'),
        total_delivery=Sum('delivery_total'),
        total_pos=Sum('pos_amount'),
        total_sales=Sum('total_sales'),
    )

    for key in totals:
        totals[key] = totals[key] or 0

    grand_total = totals['total_sales']

    context = {
        'sales': sales,
        'totals': totals,
        'grand_total': grand_total,
        'start': start,
        'end': end,
        'month': month,
        'branch': branch_name,
    }

    # ===== Generate PDF =====
    pdf = generate_pdf("sales/sales_report_export.html", context)

    # ===== Send Action =====
    if request.method == "POST":
        send_via = request.POST.get("send_via")
        email = (request.POST.get("email") or "").strip()
        number = (request.POST.get("whatsapp") or "").strip()

        # ===== Email Validation =====
        if send_via == "email":
            if not email:
                messages.error(request, "Please enter Email.")
                return redirect(f"{reverse('export_report_page', args=[report_type])}?{query_params}")

            send_email_report(
                email,
                "Sales Report",
                f"Total Sales: {grand_total}",
                pdf
            )
            messages.success(request, "Sales report sent via Email.")
            return redirect(f"{reverse('history_sales')}?{query_params}")

        # ===== WhatsApp Validation =====
        elif send_via == "whatsapp":
            if not number:
                messages.error(request, "Please enter WhatsApp number.")
                return redirect(f"{reverse('export_report_page', args=[report_type])}?{query_params}")

            # Format validation
            try:
                phone_validator(number)
            except ValidationError as e:
                messages.error(request, e.message)
                return redirect(f"{reverse('export_report_page', args=[report_type])}?{query_params}")

            # Generate PDF link
            pdf_link = save_pdf_and_get_link(request, pdf)

            message = (
                f"Sales Report Total: {grand_total}\n"
                f"Download PDF: {pdf_link}"
            )

            return send_whatsapp(number, message)

    # ===== Open Export Page =====
    return render(request, "reports/export_page.html", {
        'report_type': report_type,
        'query_params': query_params,
        'action_url': reverse('send_sales_report')
    })