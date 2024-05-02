from django.contrib import admin
from django.urls import path, include
from embed import views as embed_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('app/', include('embed.urls')),
]
