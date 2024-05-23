import json
import tempfile
import os
import base64
from io import BytesIO
from PIL import Image
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .qr_embed import generate_qr
from .qr_embed import apply_watermark


@csrf_exempt
@require_http_methods(["POST"])
def receive_and_process_qrdata(request):
    data = json.loads(request.body)
    qr_id = data.get('id')
    qr_date = data.get('date')

    # id + date
    data_str = str(qr_id) + str(qr_date)
    data = int(data_str)

    # qr image 생성
    qr_image = generate_qr(data)

    # QR코드 이미지를 바이너리 데이터로 클라이언트에 전송
    response = HttpResponse(content_type="image/png")
    qr_image.save(response, "PNG")
    return response

@csrf_exempt
@require_http_methods(["POST"])
def receive_original_image(request):
    bg_img = request.FILES.get('background_img', None)
    wm_img = request.FILES.get('wm_img', None)
    if bg_img and wm_img:
        # 배경 이미지 처리
        bg_img_data = bg_img.read()
        bg_img_obj = Image.open(BytesIO(bg_img_data)).convert('RGB')
        # 워터마크 이미지 처리
        wm_img_data = wm_img.read()
        wm_img_obj = Image.open(BytesIO(wm_img_data)).convert('RGB')

        # 워터마크 적용
        success, watermarked_image_bytes = apply_watermark(bg_img_obj, wm_img_obj)

        if success:
            # 인코딩된 바이트 데이터를 HTTP 응답으로 전송
            response = HttpResponse(watermarked_image_bytes.tobytes(), content_type="image/png")
            return response
        else:
            return HttpResponse("Image encoding failed", status=500)
    else:
        return HttpResponse("No image provided or QR image not found", status=400)
