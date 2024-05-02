from django.urls import path
from . import views

app_name = 'embed'

urlpatterns = [
    path('embed/qr_data/', views.receive_and_process_qrdata, name='qrdata'),
    path('embed/watermark_img/', views.receive_original_image, name='watermarked_img'),
]
