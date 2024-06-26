# QRCode 삽입하기
import qrcode
from PIL import Image
import numpy as np
import cv2
import pywt

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
Embed watermark img to custom img
"""

def apply_watermark(original_image, watermark_image):
    def embed_watermark(block, watermark, index):
        GV = 30
        watermark_index = index

        C_f = block[1, 0]
        C_r = block[0, 1]
        M = (C_f + C_r) / 2
        D = np.abs(C_f - C_r)
        array = [GV + D, 50]

        if watermark[watermark_index] == 255:
            C_f = M + np.min(array)
            C_r = M - np.min(array)
        else:
            C_f = M - np.min(array)
            C_r = M + np.min(array)

        block[1, 0] = C_f
        block[0, 1] = C_r

        return block

    # PIL 이미지를 numpy 배열로 변환하고 RGB에서 BGR로 변환
    original_image = cv2.cvtColor(np.array(original_image), cv2.COLOR_RGB2BGR)
    watermark_image = cv2.cvtColor(np.array(watermark_image), cv2.COLOR_RGB2BGR)

    if watermark_image.shape[0] != 64 or watermark_image.shape[1] != 64:
        # 워터마크 이미지가 64x64 픽셀이 아닐 경우 리사이징
        watermark_image = cv2.resize(watermark_image, (64, 64), interpolation=cv2.INTER_AREA)

    # 이미지를 읽고 그레이스케일로 변환
    #original_image = original_image

    yuv_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2YUV)
    y_channel, u_channel, v_channel = cv2.split(yuv_image)

    # 워터마크 이미지 불러오기 (그레이스케일)
    watermark = cv2.cvtColor(watermark_image, cv2.COLOR_BGR2GRAY)

    # 이진화된 이미지를 배열로 변환
    watermark = np.array(watermark)
    # 이미지 이진화
    _, watermark = cv2.threshold(watermark, 128, 255, cv2.THRESH_BINARY)
    watermark = watermark.reshape(-1)
    # cv2.imshow("watermark", watermark)

    coeffs = pywt.dwt2(y_channel, 'haar')
    LL, (LH, HL, HH) = coeffs

    # 2차원 DCT를 적용할 블록의 크기를 정의 (예: 8x8)
    block_size = 8

    # 이미지를 block_size x block_size 블록으로 나누고, 각 블록에 대해 DCT 적용
    index = 0
    # print("watermark.size: ", watermark.size)
    for i in range(0, HL.shape[0], block_size):
        for j in range(0, HL.shape[1], block_size):
            if index > watermark.size - 1: break;

            block = HL[i:i + block_size, j:j + block_size].astype(np.float32)

            # 실제 블록 크기 확인
            actual_block_size = block.shape
            if actual_block_size == (block_size, block_size):
                # 2차원 DCT 적용
                dct_block = cv2.dct(block)

                # 워터마킹 과정
                dct_block = embed_watermark(dct_block, watermark, index)

                # 2차원 IDCT로 원래 공간으로 되돌림
                idct_block = cv2.idct(dct_block)
                HL[i:i + block_size, j:j + block_size] = idct_block
            else:
                # 크기가 (8, 8)이 아닌 블록은 변환 없이 그대로 유지
                continue

            index += 1

    reconstructed_y_channel = pywt.idwt2((LL, (LH, HL, HH)), 'haar')
    # 결과 이미지를 uint8 타입으로 변환 및 범위 조정
    reconstructed_y_channel = np.clip(reconstructed_y_channel, 0, 255).astype(np.uint8)
    reconstructed_y_channel_resized = cv2.resize(reconstructed_y_channel, (u_channel.shape[1], u_channel.shape[0]))

    # YUV 채널 재결합 및 RGB로 변환
    reconstructed_image = cv2.merge([reconstructed_y_channel_resized, u_channel, v_channel])
    reconstructed_image = cv2.cvtColor(reconstructed_image, cv2.COLOR_YUV2BGR)

    # 이미지를 인코딩하여 반환
    success, encoded_image = cv2.imencode('.png', reconstructed_image)
    if success:
        return True, encoded_image
    else:
        return False, None

