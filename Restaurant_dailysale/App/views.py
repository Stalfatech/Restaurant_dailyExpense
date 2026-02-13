
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
                    user_type=1   # MANAGER
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

    return render(request, 'Admin/add_manager.html')

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
