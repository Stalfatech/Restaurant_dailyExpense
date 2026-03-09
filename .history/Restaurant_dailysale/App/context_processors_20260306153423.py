from .models import DashboardProfile

def dashboard_profile_data(request):
    profile = DashboardProfile.objects.first()
    return {
        'dashboard_profile': profile
    }
    
    
    
# context_processors.py
# context_processors.py
from .models import Notification

def notifications_processor(request):
    """
    Provides notifications to all templates safely.
    Admins see last 5 notifications.
    Managers see their own last 5 notifications.
    """
    if request.user.is_authenticated:
        if request.user.user_type == 0:  # Admin
            notifications = Notification.objects.order_by('-created_at')[:5]
            count = notifications.count()
        else:  # Manager or other user
            notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
            count = notifications.count()
    else:
        notifications = []
        count = 0

    return {
        "notifications": notifications,
        "notification_count": count
    }