from rest_framework.views import APIView
from rest_framework.response import Response
from .watermark_extractor import extract_watermark
import base64

class ImageProcessView(APIView):
    def post(self, request, *args, **kwargs):
        image = request.FILES.get('imageFile')
        if image:
            # 이미지 파일 저장
            print(f"Received image name: {image.name}")  # 로그로 파일 이름 출력
            save_path = 'image/' + image.name
            with open(save_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            # 워터마크 추출
            buffer, decoded_data = extract_watermark(save_path)

            user_id = decoded_data[:8]
            date = decoded_data[8:]

            # Base64 인코딩 문자열로 변환
            watermark_base64 = base64.b64encode(buffer).decode()

            # Base64 문자열을 응답으로 전송
            return Response({
                'message': 'Image processed',
                'watermark': watermark_base64,
                'userId' : user_id,
                'date' : date,
            })
        else:
            return Response({'error': 'No image file provided'}, status=400)
