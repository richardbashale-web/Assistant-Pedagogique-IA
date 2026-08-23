import os
import sys
import django

sys.path.append('c:\\Users\\hp\\.antigravity-ide\\Assistant pédagogique\\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from users.models import User, Student
from users.views import dashboard_stats
from django.test import RequestFactory

rf = RequestFactory()
user = User.objects.filter(profile__role__nom='etudiant').first()
if not user:
    user = User.objects.first()

request = rf.get('/api/dashboard_stats/')
request.user = user

try:
    response = dashboard_stats(request)
    print("Response status:", response.status_code)
    print("Response data:", response.data)
except Exception as e:
    import traceback
    traceback.print_exc()

