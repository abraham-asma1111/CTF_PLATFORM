from django.contrib.auth.models import User
from challenges.models import Challenge


def footer_stats(request):
    """
    Context processor to provide dynamic footer statistics
    """
    return {
        'total_challenges': Challenge.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
    }
