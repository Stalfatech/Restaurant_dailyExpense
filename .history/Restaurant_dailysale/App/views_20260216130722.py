
from .models import  User,Register,Manager,Staff
from django.contrib.auth.hashers import make_password,check_password
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from datetime import date
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.conf import settings
from .forms import LoginForm,ForgotPasswordForm,ResetPasswordForm
from django.conf import settings
from django.db import transaction 
from .models import  User,Register,Manager,Branch,Expense,CashBook
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Subquery



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

    elif user.user_type == 1:  # Manager
        expenses = Expense.objects.filter(date=today, branch=user.branch)
        sales = DailySale.objects.filter(date=today, branch=user.branch)

        monthly_sales_qs = DailySale.objects.filter(branch=user.branch).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('total_sales')
        ).order_by('month')

    else:
        expenses = Expense.objects.none()
        sales = DailySale.objects.none()
        monthly_sales_qs = []

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
        total_breakfast=Sum('breakfast'),
        total_lunch=Sum('lunch'),
        total_dinner=Sum('dinner'),
        total_delivery=Sum('delivery'),
        total_pos=Sum('pos_amount'),
        total_cash=Sum('cash_sales'),
        total_sales=Sum('total_sales'),
    )

    # Replace None with 0
    for key in totals:
        totals[key] = totals[key] or 0

    return render(request, 'content_dash.html', {
        'daily_total': daily_total,
        'daily_sales_total': daily_sales_total,
        'net_profit': net_profit,
        'expenses': expenses,
        'sales': sales,
        'totals': totals,              # For today's sales table/card
        'monthly_sales': monthly_sales,  # For chart
    })


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

@never_cache
def add_manager(request):
    if request.session.get('usertype') != 0:
        return redirect('no_permission')

    branches = Branch.objects.all()
    if request.method == "POST":

        name = request.POST.get('name')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        address = request.POST.get('address')
        joining_date = request.POST.get('joining_date')
        email = request.POST.get('gmail')
        password = request.POST.get('password')
        photo = request.FILES.get('photo')
        branch_id = request.POST.get('branch')

        # 🔍 VALIDATION
        if not email or not password:
            messages.error(request, "Email and password are required")
        if not all([name, phone, dob, address, joining_date, email, password, branch_id]):
            messages.error(request, "All mandatory fields are required")
            return redirect('manager_add')
          

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('manager_add')

        try:
            with transaction.atomic():
                branch = Branch.objects.get(id=branch_id)

                # ✅ 1. CREATE USER
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    name=name,
                    user_type=1,
                     branch=branch# MANAGER
                )

                # ✅ 2. CREATE REGISTER
                Register.objects.create(
                    name=name,
                    contact=phone,
                    loginid=user
                )

                # ✅ 3. CREATE MANAGER PROFILE  🔥 (THIS WAS MISSING)
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
            return redirect('manager_add')

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
        try:
            with transaction.atomic():

                # Update User table
                manager.user.name = request.POST.get('name')
                manager.user.email = request.POST.get('email')
                name = request.POST.get('name')
                email = request.POST.get('email')
                phone = request.POST.get('phone')
                dob = request.POST.get('dob')
                gender = request.POST.get('gender')
                joining_date = request.POST.get('joining_date')
                address = request.POST.get('address')
                branch_id = request.POST.get('branch')

                # 🔴 Validation
                if not all([name, email, phone, branch_id]):
                    messages.error(request, "All mandatory fields are required")
                    return redirect('manager_edit', id=id)

                branch = Branch.objects.get(id=branch_id)

                # ✅ Update User
                manager.user.name = name
                manager.user.email = email
                manager.user.branch = branch
                manager.user.save()

                # Update Manager table
                manager.phone = request.POST.get('phone')
                manager.dob = request.POST.get('dob')
                manager.gender = request.POST.get('gender')
                manager.address = request.POST.get('address')
                manager.joining_date = request.POST.get('joining_date')
                 # ✅ Update Manager profile
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
            return redirect('manager_view')

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

    # Get selected date from GET params (optional)
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = None  # show all if no date selected

    # Base queryset
    if user.user_type == 0:  # Admin sees all branches
        expenses = Expense.objects.all()
    else:  # Manager sees only their branch
        expenses = Expense.objects.filter(branch=user.branch)

    # Filter by date if selected
    if selected_date:
        expenses = expenses.filter(date=selected_date)

    # Calculate total
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


@admin_or_manager_required
def add_expense(request):
    user = request.user
    today = date.today()

    # Determine branch first
    if user.user_type == 0:  # Admin
        branch = None  # Admin selects from form
    else:
        branch = user.branch

        if not branch:
            messages.error(request, "You are not assigned to any branch.")
            return redirect('dashboard_expenses')

        # 🔒 Check if day closed
        if CashBook.objects.filter(
            date=today,
            branch=branch,
            is_closed=True
        ).exists():
            messages.error(request, "Day is closed. No modifications allowed.")
            return redirect('dashboard_expenses')

    form = ExpenseForm(request.POST or None, request.FILES or None, user=user)

    if form.is_valid():
        expense = form.save(commit=False)

        if user.user_type == 0:
            expense.branch = form.cleaned_data.get('branch')
            expense.status = form.cleaned_data.get('status') or 'Approved'
        else:
            expense.branch = branch
            expense.status = 'Pending'

        expense.created_by = user
        expense.save()

        # 🔄 UPDATE CASHBOOK ONLY IF APPROVED
        if expense.status == "Approved":
            update_cashbook(expense.branch, expense.date)

        messages.success(request, "Expense added successfully.")
        return redirect('dashboard_expenses')

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'user_type': user.user_type,
        'page_title': 'Add Expense'
    })

from datetime import timedelta


def get_opening_balance(branch, selected_date):

    previous_day = selected_date - timedelta(days=1)

    previous_cashbook = CashBook.objects.filter(
        branch=branch,
        date=previous_day
    ).first()

    if previous_cashbook:
        return previous_cashbook.closing_balance

    return Decimal('0.00')


def update_cashbook(branch, selected_date):
    
    cashbook, created = CashBook.objects.get_or_create(
        branch=branch,
        date=selected_date
    )

    # ✅ Always set opening balance from previous day
    cashbook.opening_balance = get_opening_balance(branch, selected_date)

    # 🔹 Total cash sales
    total_cash = DailySale.objects.filter(
        branch=branch,
        date=selected_date
    ).aggregate(total=Sum('cash_sales'))['total'] or Decimal('0.00')

    # 🔹 Approved expenses
    total_expenses = Expense.objects.filter(
        branch=branch,
        date=selected_date,
        status="Approved"
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    cashbook.cash_sales = total_cash
    cashbook.expenses = total_expenses

    # 🔹 Closing formula
    cashbook.closing_balance = (
        cashbook.opening_balance +
        cashbook.cash_sales -
        cashbook.expenses
    )

    cashbook.save()





@admin_or_manager_required
def close_day(request):

    user = request.user

    if user.user_type == 0:
        messages.error(request, "Admin must select branch.")
        return redirect('cashbook_dashboard')

    branch = user.branch
    today = date.today()

    cashbook = CashBook.objects.filter(
        branch=branch,
        date=today
    ).first()

    if not cashbook:
        messages.error(request, "No transactions for today.")
        return redirect('cashbook_dashboard')

    if cashbook.is_closed:
        messages.warning(request, "Day already closed.")
        return redirect('cashbook_dashboard')

    # Recalculate before closing
    update_cashbook(branch, today)

    cashbook.is_closed = True
    cashbook.save()

    messages.success(request, "Day Closed Successfully ✅")
    return redirect('cashbook_dashboard')


# ================= EDIT EXPENSE =================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date
from .forms import ExpenseForm
from .models import Expense, CashBook
from .decorators import admin_or_manager_required

# views.py
@admin_or_manager_required
def edit_expense(request, pk):
    user = request.user  # always logged-in

    # Fetch expense based on role
    if user.user_type == 0:  # Admin can edit any expense
        expense = get_object_or_404(Expense, pk=pk)
    else:  # Manager can edit only their branch
        expense = get_object_or_404(Expense, pk=pk, branch=user.branch)

    # Check if day is closed
    if CashBook.objects.filter(date=expense.date, branch=expense.branch, is_closed=True).exists():
        messages.error(request, "Day is closed. Cannot edit expense.")
        return redirect('dashboard_expenses')

    form = ExpenseForm(
    request.POST or None,
    request.FILES or None,
    instance=expense,
    user=user
)


    if form.is_valid():
        updated_expense = form.save(commit=False)

        # Branch and status logic
        if user.user_type == 0:  # Admin
            branch = form.cleaned_data.get('branch')
            if not branch:
                messages.error(request, "Please select a branch for the expense.")
                return render(request, 'expenses/expense_form.html', {'form': form, 'user_type': user.user_type})
            updated_expense.branch = branch
            updated_expense.status = form.cleaned_data.get('status') or updated_expense.status
        else:  # Manager
            updated_expense.branch = user.branch
            # Keep status as-is, manager cannot approve
            updated_expense.status = expense.status

        updated_expense.save()
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

    if request.method == "POST":
        expense.delete()
        return redirect('dashboard_expenses')

    return render(request, 'expenses/delete_confirm.html', {'expense': expense})


# ================= HISTORY =================

@admin_or_manager_required
def history_expenses(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    month = request.GET.get('month')  # e.g., "2026-02"

    if request.user.user_type == 0:
        expenses = Expense.objects.all()
    else:
        expenses = Expense.objects.filter(branch=request.user.branch)

    if start and end:
        expenses = expenses.filter(date__range=[start, end])

    if month:
        # Split "YYYY-MM" into year and month
        try:
            year, month_num = map(int, month.split('-'))
            expenses = expenses.filter(date__year=year, date__month=month_num)
        except ValueError:
            pass  # ignore invalid input

    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'expenses/history.html', {
        'expenses': expenses,
        'total': total,
        'selected_month': month,  # optional if you want to keep it
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
    selected_role = request.GET.get('role')

    # Base queryset
    if user.user_type == 0:  # Admin
        staffs = Staff.objects.select_related('created_by', 'branch')
    else:  # Manager
        staffs = Staff.objects.select_related('created_by', 'branch').filter(
            branch=user.branch
        )

    # Role filter
    if selected_role:
        staffs = staffs.filter(role=selected_role)

    staffs = staffs.order_by('id')

    # Unique roles for dropdown
    if user.user_type == 0:
        roles = Staff.objects.values_list('role', flat=True).distinct()
    else:
        roles = Staff.objects.filter(
            branch=user.branch
        ).values_list('role', flat=True).distinct()

    return render(request, 'Admin/stafflist_view.html', {
        'staffs': staffs,
        'roles': roles,
        'selected_role': selected_role
    })




from .models import DailySale, CashBook
from .forms import DailySaleForm
from datetime import date
from django.contrib import messages
from django.db.models import Sum


@admin_or_manager_required
def add_daily_sale(request):

    user = request.user
    form = DailySaleForm(request.POST or None, user=user)

    if form.is_valid():

        sale = form.save(commit=False)

        # Assign branch
        if user.user_type == 0:
            sale.branch = form.cleaned_data.get('branch')
        else:
            if not user.branch:
                messages.error(request, "You are not assigned to any branch.")
                return redirect('daily_sales_dashboard')
            sale.branch = user.branch

        sale.created_by = user
        sale.save()

        # 🔄 Update CashBook
        cashbook, created = CashBook.objects.get_or_create(
            date=sale.date,
            branch=sale.branch
        )

        # If new record, set opening balance
        if created:
            cashbook.opening_balance = get_opening_balance(
                sale.branch,
                sale.date
            )

        # Always recalculate total cash
        total_cash = DailySale.objects.filter(
            branch=sale.branch,
            date=sale.date
        ).aggregate(total=Sum('cash_sales'))['total'] or 0

        cashbook.cash_sales = total_cash

        # Calculate closing
        cashbook.closing_balance = (
            cashbook.opening_balance +
            cashbook.cash_sales -
            cashbook.expenses
        )

        cashbook.save()

        messages.success(request, "Daily sale added successfully ✅")
        return redirect('daily_sales_dashboard')

    return render(request, 'sales/daily_sale_form.html', {
        'form': form,
        'user_type': user.user_type,
        'page_title': 'Add Daily Sale'
    })


from django.db.models import Sum
from datetime import datetime, date

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

    if user.user_type == 0:  # Admin
        sales = DailySale.objects.filter(date=selected_date)
    else:  # Manager
        if not user.branch:
            sales = DailySale.objects.none()
        else:
            sales = DailySale.objects.filter(
                date=selected_date,
                branch=user.branch
            )

    totals = sales.aggregate(
        total_breakfast=Sum('breakfast'),
        total_lunch=Sum('lunch'),
        total_dinner=Sum('dinner'),
        total_delivery=Sum('delivery'),
        total_pos=Sum('pos_amount'),
        total_cash=Sum('cash_sales'),
        total_sales=Sum('total_sales'),
    )

    for key in totals:
        totals[key] = totals[key] or 0

    return render(request, 'sales/daily_dashboard.html', {
        'sales': sales,
        'totals': totals,
        'selected_date': selected_date
    })


@admin_or_manager_required
def edit_daily_sale(request, pk):
    user = request.user
    sale = get_object_or_404(DailySale, pk=pk)

    # 🔒 Prevent editing if day is closed
    if CashBook.objects.filter(
        date=sale.date,
        branch=getattr(sale.branch, 'id', None),
        is_closed=True
    ).exists():
        messages.error(request, "Day is closed. Cannot edit sales.")
        return redirect('daily_sales_dashboard')

    # Bind form
    form = DailySaleForm(request.POST or None, instance=sale, user=user)

    if form.is_valid():
        updated_sale = form.save(commit=False)

        # Set branch based on user type
        if user.user_type == 0:  # Admin
            updated_sale.branch = form.cleaned_data.get('branch')
        else:  # Manager
            if not user.branch:
                messages.error(request, "You are not assigned to any branch.")
                return redirect('daily_sales_dashboard')
            updated_sale.branch = user.branch

        updated_sale.created_by = user
        updated_sale.save()

        # 🔄 Update CashBook for that date and branch
        cashbook, created = CashBook.objects.get_or_create(
            date=updated_sale.date,
            branch=updated_sale.branch
        )

        cashbook.cash_sales = (
            (updated_sale.breakfast or 0) +
            (updated_sale.lunch or 0) +
            (updated_sale.dinner or 0) +
            (updated_sale.delivery or 0)
        )
        cashbook.save()

        messages.success(request, "Daily sale updated successfully ✅")
        return redirect('daily_sales_dashboard')

    return render(request, 'sales/daily_sale_form.html', {
        'form': form,
        'user_type': user.user_type,
        'page_title': 'Edit Daily Sale'
    })



from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum

@admin_or_manager_required
def delete_daily_sale(request, pk):
    user = request.user
    sale = get_object_or_404(DailySale, pk=pk)

    # Permission check
    if user.user_type != 0 and sale.branch != user.branch:
        messages.error(request, "You are not allowed to delete this sale.")
        return redirect('daily_sales_dashboard')

    # Prevent if day closed
    if CashBook.objects.filter(
        date=sale.date,
        branch=sale.branch,
        is_closed=True
    ).exists():
        messages.error(request, "Day is closed. Cannot delete sales.")
        return redirect('daily_sales_dashboard')

    if request.method == "POST":
        sale_date = sale.date
        sale_branch = sale.branch
        sale.delete()

        # Recalculate CashBook
        total_cash = DailySale.objects.filter(
            date=sale_date,
            branch=sale_branch
        ).aggregate(
            total=Sum('cash_sales')
        )['total'] or 0

        cashbook = CashBook.objects.filter(
            date=sale_date,
            branch=sale_branch
        ).first()

        if cashbook:
            cashbook.cash_sales = total_cash
            cashbook.save()

        messages.success(request, "Daily sale deleted successfully ✅")
        return redirect('daily_sales_dashboard')

    return render(request, 'sales/delete_daily_sale.html', {
        'sale': sale
    })




from django.db.models import Sum
from datetime import datetime
from django.contrib.auth.decorators import login_required

from django.db.models import Sum
from datetime import datetime
@admin_or_manager_required
def history_sales(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    month = request.GET.get('month')  # NEW

    user = request.user

    # Admin → all branches
    if user.user_type == 0:
        sales = DailySale.objects.all()
    else:
        if not user.branch:
            sales = DailySale.objects.none()
        else:
            sales = DailySale.objects.filter(branch=user.branch)

    # Month filter overrides start/end
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            sales = sales.filter(date__year=year, date__month=month_num)
        except ValueError:
            pass
    # Date range filter (only if month not set)
    elif start and end:
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            sales = sales.filter(date__range=[start_date, end_date])
        except ValueError:
            pass

    # Aggregate totals
    totals = sales.aggregate(
        total_breakfast=Sum('breakfast'),
        total_lunch=Sum('lunch'),
        total_dinner=Sum('dinner'),
        total_delivery=Sum('delivery'),
        total_pos=Sum('pos_amount'),
        total_sales=Sum('total_sales'),
    )

    for key in totals:
        totals[key] = totals[key] or 0

    grand_total = totals['total_sales']

    return render(request, 'sales/history.html', {
        'sales': sales.order_by('-date'),
        'totals': totals,
        'grand_total': grand_total,
    })



from datetime import date, datetime

@admin_or_manager_required
def cashbook_dashboard(request):

    selected_date = request.GET.get('date')

    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    user = request.user

    if user.user_type == 0:  # Admin
        cashbooks = CashBook.objects.filter(date=selected_date)
    else:  # Manager
        cashbooks = CashBook.objects.filter(
            branch=user.branch,
            date=selected_date
        )

    return render(request, "cashbook/dashboard.html", {
        "cashbooks": cashbooks,
        "selected_date": selected_date
    })
