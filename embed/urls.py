from django.urls import path
from . import views

app_name = 'embed'

urlpatterns = [
    path('qr_data/', views.receive_and_process_qrdata, name='qrdata'),
    path('watermark_img/', views.receive_original_image, name='watermark_img'),
]
