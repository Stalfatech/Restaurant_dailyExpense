from django.shortcuts import redirect

def admin_or_manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.user_type in [0, 2]:  # Admin or Manager
            return view_func(request, *args, **kwargs)

        return redirect('no_permission')

    return wrapper
