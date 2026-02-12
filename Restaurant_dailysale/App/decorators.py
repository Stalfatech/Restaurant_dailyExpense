from functools import wraps
from django.shortcuts import redirect

def admin_or_manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.user_type not in [0, 1]:  # Admin=0, Manager=1
            return redirect('no_permission')
        return view_func(request, *args, **kwargs)
    return wrapper