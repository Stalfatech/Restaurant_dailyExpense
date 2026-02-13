
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
    
import os
import tempfile
from django.http import JsonResponse
from .y import extract_amount_from_invoice


def extract_invoice_amount_ajax(request):
    if request.method == "POST" and request.FILES.get("invoice"):

        invoice_file = request.FILES["invoice"]

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in invoice_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name

        try:
            amount = extract_amount_from_invoice(temp_path)
        finally:
            os.remove(temp_path)

        return JsonResponse({
            "amount": amount if amount else ""
        })

    return JsonResponse({"error": "Invalid request"}, status=400)




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

from datetime import date
from django.contrib import messages
from django.shortcuts import redirect, render
from django.db import transaction
from .utils.invoice_parser import extract_amount_from_invoice


@admin_or_manager_required
def add_expense(request):
    user = request.user

    # 🔒 Prevent adding expense if day closed
    if CashBook.objects.filter(
        date=date.today(),
        branch=getattr(user, 'branch', None),
        is_closed=True
    ).exists():
        messages.error(request, "Day is closed. No modifications allowed.")
        return redirect('dashboard_expenses')

    form = ExpenseForm(request.POST or None, request.FILES or None, user=user)

    if form.is_valid():
        try:
            with transaction.atomic():

                expense = form.save(commit=False)

                # 👤 Branch & Status Logic
                if user.user_type == 0:  # Admin
                    expense.branch = form.cleaned_data.get('branch')
                    expense.status = form.cleaned_data.get('status') or 'Approved'
                else:  # Manager
                    if not user.branch:
                        messages.error(request, "You are not assigned to any branch.")
                        return redirect('dashboard_expenses')
                    expense.branch = user.branch
                    expense.status = 'Pending'

                expense.created_by = user

                # ✅ STEP 1: Save first (very important for invoice file)
                expense.save()

                # ✅ STEP 2: Extract amount after file is saved
                if expense.invoice:
                    try:
                        extracted_amount = extract_amount_from_invoice(
                            expense.invoice.path
                        )

                        if extracted_amount:
                            expense.amount = extracted_amount
                            expense.save(update_fields=['amount'])

                    except Exception as e:
                        print("OCR Error:", e)
                        # Don't block saving, just notify
                        messages.warning(
                            request,
                            "Invoice uploaded but amount could not be auto-extracted."
                        )

                messages.success(request, "Expense added successfully.")
                return redirect('dashboard_expenses')

        except Exception as e:
            messages.error(request, f"Error saving expense: {str(e)}")

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'user_type': user.user_type
    })




def close_day(request):
    cashbook = get_object_or_404(
    CashBook,
    date=date.today(),
    branch=request.user.branch
)


    cashbook.calculate_closing()
    cashbook.is_closed = True
    cashbook.save()

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

    form = ExpenseForm(request.POST or None, request.FILES or None, instance=expense)

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
        'user_type': user.user_type
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

    if request.user.user_type == 0:
        expenses = Expense.objects.all()
    else:
     expenses = Expense.objects.filter(
        branch=request.user.branch
     )


    if start and end:
        expenses = expenses.filter(date__range=[start, end])

    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'expenses/history.html', {
        'expenses': expenses,
        'total': total
    })
@admin_or_manager_required
def approve_expense(request, pk):

    if request.user.user_type != 0:
        return redirect('no_permission')

    expense = get_object_or_404(Expense, pk=pk)
    expense.status = 'Approved'
    expense.save()

    return redirect('dashboard_expenses')




# ================= SUPPLIER =================

@login_required
@admin_or_manager_required
def add_supplier(request):
    form = SupplierForm(request.POST or None)
    if form.is_valid():
        form.save()
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
        return redirect('product_list')
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

def add_staff(request):
    if request.method == "POST":
        staff_id = request.POST.get('staff_id')
        name = request.POST.get('name')
        role = request.POST.get('role')
        contact = request.POST.get('contact')
        dob = request.POST.get('dob')
        joining_date = request.POST.get('joining_date')
        salary_type = request.POST.get('salary_type')
        status = request.POST.get('status')

        # 🔴 Check Duplicate Staff ID
        if Staff.objects.filter(staff_id=staff_id).exists():
            messages.error(request, "Staff ID already exists.")
            return redirect('add_staff')

        # 🔴 Contact Validation
        if not contact or not contact.isdigit() or len(contact) != 10:
            messages.error(request, "Contact number must be exactly 10 digits.")
            return redirect('add_staff')

        # 🔴 DOB Future Validation
        if dob:
            dob_date = date.fromisoformat(dob)
            if dob_date > date.today():
                messages.error(request, "Date of Birth cannot be in the future.")
                return redirect('add_staff')

        # 🟢 Save Staff
        Staff.objects.create(
            staff_id=staff_id,
            name=name,
            role=role,
            contact=contact,
            dob=dob if dob else None,
            joining_date=joining_date,
            salary_type=salary_type,
            status=status
        )

        messages.success(request, "Staff added successfully ✅")
        return redirect('staff_list')

    return render(request, 'Manager/staff_add.html')

def staff_list(request):
    staffs = Staff.objects.all().order_by('id')
    return render(request, 'Manager/staff_list.html', {'staffs': staffs})

def staff_list(request):
    role_filter = request.GET.get('role')

    staffs = Staff.objects.all().order_by('id')   # Correct order 1 → last

    if role_filter:
        staffs = staffs.filter(role=role_filter)

    # Get distinct roles for dropdown
    roles = Staff.objects.values_list('role', flat=True).distinct()

    context = {
        'staffs': staffs,
        'roles': roles,
        'selected_role': role_filter
    }

    return render(request, 'Manager/staff_list.html', context)

def edit_staff(request, id):
    staff = get_object_or_404(Staff, id=id)

    if request.method == "POST":
        staff_id = request.POST.get('staff_id')
        name = request.POST.get('name')
        role = request.POST.get('role')
        contact = request.POST.get('contact')
        dob = request.POST.get('dob')
        joining_date = request.POST.get('joining_date')
        salary_type = request.POST.get('salary_type')
        status = request.POST.get('status')

        # Duplicate Staff ID check (except current staff)
        if Staff.objects.filter(staff_id=staff_id).exclude(id=id).exists():
            messages.error(request, "Staff ID already exists.")
            return redirect('edit_staff', id=id)

        # Contact Validation
        if not contact or not contact.isdigit() or len(contact) != 10:
            messages.error(request, "Contact number must be exactly 10 digits.")
            return redirect('edit_staff', id=id)

        # DOB Validation
        if dob:
            dob_date = date.fromisoformat(dob)
            if dob_date > date.today():
                messages.error(request, "Date of Birth cannot be in the future.")
                return redirect('edit_staff', id=id)

        # Update Staff
        staff.staff_id = staff_id
        staff.name = name
        staff.role = role
        staff.contact = contact
        staff.dob = dob if dob else None
        staff.joining_date = joining_date
        staff.salary_type = salary_type
        staff.status = status
        staff.save()

        messages.success(request, "Staff updated successfully ✅")
        return redirect('staff_list')

    return render(request, 'Manager/staff_edit.html', {'staff': staff})

def delete_staff(request, id):
    staff = get_object_or_404(Staff, id=id)

    staff.delete()

    messages.success(request, "Staff deleted successfully 🗑️")
    return redirect('staff_list')
