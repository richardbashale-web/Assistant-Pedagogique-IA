import os
import sys
import django

sys.path.append('c:\\Users\\hp\\.antigravity-ide\\Assistant pédagogique\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from users.models import User
from users.views import CurrentUserView, dashboard_stats
from rest_framework.test import APIRequestFactory, force_authenticate

factory = APIRequestFactory()

user = User.objects.filter(profile__role__nom='etudiant').first()
if not user:
    user = User.objects.first()

request_me = factory.get('/api/me/')
force_authenticate(request_me, user=user)

view = CurrentUserView.as_view()
try:
    response = view(request_me)
    print("ME Response status:", response.status_code)
except Exception as e:
    import traceback
    print("ME ERROR:")
    traceback.print_exc()

request_dash = factory.get('/api/dashboard_stats/')
force_authenticate(request_dash, user=user)
try:
    response2 = dashboard_stats(request_dash)
    print("DASHBOARD Response status:", response2.status_code)
except Exception as e:
    import traceback
    print("DASHBOARD ERROR:")
    traceback.print_exc()

