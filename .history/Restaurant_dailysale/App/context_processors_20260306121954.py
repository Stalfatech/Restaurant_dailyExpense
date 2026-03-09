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