from django.urls import path
from . import views

app_name = 'embed'

urlpatterns = [
    path('embed/receive_qrdata/', views.receive_qrdata, name='receive_qrdata'),
]
