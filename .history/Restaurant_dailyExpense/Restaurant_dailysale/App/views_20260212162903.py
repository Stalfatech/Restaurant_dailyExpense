
from .models import  User,Register,Manager,Branch,Expense,CashBook
from django.contrib.auth.hashers import make_password,check_password
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages

from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.conf import settings
from .forms import LoginForm,ForgotPasswordForm,ResetPasswordForm
from django.conf import settings
from django.db import transaction 


def dashboard(request):
    return render(request, 'content_dash.html')

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

            if user is None:
                messages.error(request, 'Invalid email')
                return redirect('login')

            if not check_password(password, user.password):
                messages.error(request, 'Invalid password')
                return redirect('login')

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
        branch = Branch.objects.get(id=branch_id)


        # 🔍 VALIDATION
        if not email or not password:
            messages.error(request, "Email and password are required")
            return redirect('manager_add')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('manager_add')

        try:
            with transaction.atomic():

                # ✅ 1. CREATE USER
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    name=name,
                    user_type=1 ,
                      branch=branch # MANAGER
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

    branches = Branch.objects.all()
return render(request, 'Admin/add_manager.html', {'branches': branches})


@never_cache
def manager_view(request):
    managers = Manager.objects.select_related('user').all().order_by('-id')

    return render(request, 'Admin/manager_list.html', {
        'managers': managers
    })

@never_cache
def manager_delete(request, id):
    manager = get_object_or_404(Manager, id=id)

    try:
        manager.user.delete()   # This deletes Manager also (CASCADE)
        messages.success(request, "Manager deleted successfully")
    except:
        messages.error(request, "Unable to delete manager")

    return redirect('manager_view')

@never_cache
def manager_edit(request, id):
    manager = get_object_or_404(Manager, id=id)

    if request.method == "POST":
        try:
            with transaction.atomic():

                # Update User table
                manager.user.name = request.POST.get('name')
                manager.user.email = request.POST.get('email')
                manager.user.save()

                # Update Manager table
                manager.phone = request.POST.get('phone')
                manager.dob = request.POST.get('dob')
                manager.gender = request.POST.get('gender')
                manager.address = request.POST.get('address')
                manager.joining_date = request.POST.get('joining_date')

                if request.FILES.get('photo'):
                    manager.photo = request.FILES.get('photo')

                manager.save()

            messages.success(request, "Manager updated successfully")
            return redirect('manager_view')

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('manager_view')

    return render(request, 'Admin/manager_edit.html', {
        'manager': manager
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

@admin_or_manager_required
def dashboard_expenses(request):
    selected_date = request.GET.get('date') or date.today()
    expenses = Expense.objects.filter(
    date=selected_date,
    status='Approved',
    branch=request.user.branch
)



    daily_total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'expenses/dashboard.html', {
        'expenses': expenses,
        'daily_total': daily_total,
        'selected_date': selected_date
    })


# ================= ADD EXPENSE =================

@admin_or_manager_required
def add_expense(request):
    form = ExpenseForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('dashboard_expenses')
    return render(request, 'expenses/expense_form.html', {'form': form})

def close_day(request):
    cashbook = CashBook.objects.get(
    date=date.today(),
    branch=request.user.branch
)

    cashbook.calculate_closing()
    cashbook.is_closed = True
    cashbook.save()

# ================= EDIT EXPENSE =================

@admin_or_manager_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    form = ExpenseForm(request.POST or None, request.FILES or None, instance=expense)
    if form.is_valid():
        form.save()
        return redirect('dashboard_expenses')
    return render(request, 'expenses/expense_form.html', {'form': form})


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

    expenses = Expense.objects.all()

    if start and end:
        expenses = expenses.filter(date__range=[start, end])

    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'expenses/history.html', {
        'expenses': expenses,
        'total': total
    })
def approve_expense(request, pk):
    expense = Expense.objects.get(pk=pk)
    expense.status = 'Approved'
    expense.save()
    return redirect('dashboard_expenses')



# ================= SUPPLIER =================

@admin_or_manager_required
def add_supplier(request):
    form = SupplierForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('dashboard_expenses')
    return render(request, 'expenses/supplier_form.html', {'form': form})
from django.db.models import Q 
@admin_or_manager_required
def supplier_list(request):
    query = request.GET.get('q')

    suppliers = Supplier.objects.all().order_by('-id')

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
        return redirect('dashboard_expenses')
    return render(request, 'expenses/product_form.html', {'form': form})

@admin_or_manager_required
def product_list(request):
    query = request.GET.get('q')

    products = Product.objects.select_related('supplier').all().order_by('-id')

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
        return redirect('product_list')

    return render(request, 'expenses/product_delete.html', {
        'product': product
    })
# ================= NO PERMISSION =================
def no_permission(request):
    return render(request, 'no_permission.html')
