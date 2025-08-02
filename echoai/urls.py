from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static
import tempfile  # <-- this was missing!

urlpatterns = [
    path('', views.index_view, name='index'),  # ✅ Main page
    path('process_audio/', views.index_view, name='process_audio'),
    path('run_code/', views.run_code_view, name='run_code'),  # ✅ Audio POST route
]

# 🔊 Serve audio files from system temp folder
urlpatterns += static('/audio/', document_root=tempfile.gettempdir())
