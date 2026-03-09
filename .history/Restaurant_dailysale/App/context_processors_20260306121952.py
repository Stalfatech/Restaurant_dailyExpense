from .models import DashboardProfile

def dashboard_profile_data(request):
    profile = DashboardProfile.objects.first()
    return {
        'dashboard_profile': profile
    }
    
    
    
    