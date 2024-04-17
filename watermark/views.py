from rest_framework.views import APIView
from rest_framework.response import Response
from .watermark_extractor import extract_watermark


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
            extracted_image = extract_watermark(save_path)

            # 추출된 이미지를 다루는 로직 (예: 저장 후 URL 반환)
            # 예시로, 이미지 파일의 경로를 반환
            return Response({'message': 'Image processed', 'imagePath': save_path})
        else:
            return Response({'error': 'No image file provided'}, status=400)
