from .models import DashboardProfile

def dashboard_profile_data(request):
    profile = DashboardProfile.objects.first()
    return {
        'dashboard_profile': profile
    }
    
    
    
from .models import Notification

def notifications(request):

    notifications = Notification.objects.all()[:10]

    return {
        "notifications": notifications,
        "notification_count": notifications.count()
    }
from .models import Notification

def notification_data(request):

    if request.user.is_authenticated:

        if request.user.user_type == 0:   # Admin
            notifications = Notification.objects.all()[:5]
            count = Notification.objects.count()

        else:  # Manager
            notifications = Notification.objects.filter(user=request.user)[:5]
            count = Notification.objects.filter(user=request.user).count()

    else:
        notifications = []
        count = 0

    return {
        "notifications": notifications,
        "notification_count": count
    }