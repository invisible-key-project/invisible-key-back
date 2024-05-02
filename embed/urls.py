from django.urls import path
from . import views

app_name = 'embed'

urlpatterns = [
    path('embed/qrdata/', views.receive_and_process_qrdata, name='qrdata'),
]
