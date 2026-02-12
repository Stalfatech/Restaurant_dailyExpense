from django.shortcuts import redirect

def admin_or_manager_required(view_func):
    def wrapper(request, *args, **kwargs):

        if not request.session.get('login_id'):
            request.session['next_url'] = request.path
            return redirect('login')

        user_type = request.session.get('usertype')

        # 0 = Admin
        # 1 = Manager
        if user_type in [0, 1]:
            return view_func(request, *args, **kwargs)

        return redirect('no_permission')

    return wrapper
