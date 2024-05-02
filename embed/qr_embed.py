import views

# QRCode 삽입하기
import qrcode
from PIL import Image
import numpy as np
import cv2

"""
Generate qr code img
"""
def generate_qr(data):

    # 데이터 생성
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=3,
        border=1,
    )

    # 데이터 추가
    qr.add_data(data)
    qr.make(fit=True)

    # qrcode 이미지 생성 (Pillow 이미지)
    img = qr.make_image(fill='black', back_color='white').convert('RGB')

    # Pillow 이미지를 OpenCV 형식으로 변환
    open_cv_image = np.array(img)
    # Convert RGB to BGR
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    # OpenCV를 사용하여 이미지 리사이징
    resized_image = cv2.resize(open_cv_image, (64, 64), interpolation=cv2.INTER_AREA)

    # 리사이징된 이미지를 다시 Pillow 이미지로 변환
    final_image = Image.fromarray(cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB))

    return final_image


"""
Embed qr img to custom img
"""
def embed_qr_img(img, qr):