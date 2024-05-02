import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from . import qr_embed

global qr_image
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
    qr_image = qr_embed.generate_qr(data)

    # QR코드 이미지를 바이너리 데이터로 클라이언트에 전송
    response = HttpResponse(content_type="image/png")
    qr_image.save(response, "PNG")
    return response


def receive_original_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        # 이미지 파일 받기
        img = request.FILES['image']

        # 워터마크 적용
        watermarked_image = qr_embed.apply_watermark(img, qr_image)

        # 이미지를 바이트로 변환하여 전송
        response = HttpResponse(content_type="image/png")
        watermarked_image.save(response, "PNG")
        return response
    else:
        return HttpResponse("No image provided", status=400)


