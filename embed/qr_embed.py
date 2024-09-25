# QRCode 삽입하기
import qrcode
from PIL import Image
import numpy as np
import cv2
import pywt
import random

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
    def adjust_image_size(image):
        """이미지의 가로 또는 세로 크기가 홀수일 경우 1픽셀을 빼서 짝수로 만듦"""
        height, width = image.shape[:2]
        if height % 2 != 0:
            height -= 1
        if width % 2 != 0:
            width -= 1
        return cv2.resize(image, (width, height))

    def embed_watermark(block, watermark, index):
        GV = 80
        watermark_index = index

        C_f = block[0, 1]
        C_r = block[1, 0]
        M = (C_f + C_r) / 2
        D = np.abs(C_f - C_r)
        array = [GV + D, 50]

        if watermark[watermark_index] > 128:
            C_f = M + np.min(array)
            C_r = M - np.min(array)
        else:
            C_f = M - np.min(array)
            C_r = M + np.min(array)

        block[0, 1] = C_f
        block[1, 0] = C_r

        return block

    # 이미지 읽기 및 YCbCr로 변환
    original_image = cv2.imread('white_image.jpg')
    # 이미지 크기 조정 (홀수일 경우 1픽셀 제거)
    original_image = adjust_image_size(original_image)
    ycbcr_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2YCrCb)
    y_channel, cb_channel, cr_channel = cv2.split(ycbcr_image)

    # Y채널에 DWT 적용
    coeffs2 = pywt.dwt2(y_channel, 'haar')  # DWT 수행
    LL, (LH, HL, HH) = coeffs2  # LH 대역 추출

    # 워터마크 이미지 불러오기
    watermark = cv2.imread("Qr_64.png", cv2.IMREAD_GRAYSCALE)
    _, watermark = cv2.threshold(watermark, 128, 255, cv2.THRESH_BINARY)
    watermark = watermark.reshape(-1)

    block_size = 8
    index = 0
    IDW = []

    # IDW 배열 생성 - Y채널과 Cb채널을 비교
    for i in range(0, y_channel.shape[0], block_size):
        for j in range(0, y_channel.shape[1], block_size):
            if index >= watermark.size:
                break

            y_block = y_channel[i:i + block_size, j:j + block_size].astype(np.float32)
            cb_block = cb_channel[i:i + block_size, j:j + block_size].astype(np.float32)

            if y_block.shape == (block_size, block_size) and cb_block.shape == (block_size, block_size):
                dct_y_block = cv2.dct(y_block)
                dct_cb_block = cv2.dct(cb_block)

                B_y = dct_y_block[0, 0]
                B_cb = dct_cb_block[0, 0]

                # IDW는 Y채널과 Cb채널의 DC 계수를 비교하여 0 또는 1 생성
                if B_y > B_cb:
                    IDW.append(1)
                else:
                    IDW.append(0)
                index += 1

    # IDW 배열이 워터마크 크기와 맞는지 확인하고 XOR 연산 수행
    IDW = np.array(IDW[:watermark.size])
    KEY = np.bitwise_xor(IDW, watermark)

    # 128을 기준으로 255 또는 1로 변환
    KEY = np.array([255 if value >= 128 else 0 for value in KEY])

    # 랜덤 블록 선택을 위한 난수 생성기 초기화
    random_seed = 42
    random.seed(random_seed)

    # LH 대역의 블록 위치 리스트 생성 및 셔플
    block_positions = [(i, j) for i in range(0, LH.shape[0], block_size) for j in range(0, LH.shape[1], block_size)]
    random.shuffle(block_positions)

    # LH 대역에서 KEY 삽입
    index = 0
    for pos in block_positions:
        if index >= KEY.size:
            break

        i, j = pos
        lh_block = LH[i:i + block_size, j:j + block_size].astype(np.float32)

        if lh_block.shape == (block_size, block_size):
            dct_lh_block = cv2.dct(lh_block)

            # KEY 삽입 (0,0) 위치에 삽입
            dct_lh_block = embed_watermark(dct_lh_block, KEY, index)
            LH[i:i + block_size, j:j + block_size] = cv2.idct(dct_lh_block)
            index += 1

    # IDWT(역 DWT)로 Y채널 복원
    coeffs2_modified = (LL, (LH, HL, HH))  # 수정된 LH 대역 사용
    y_channel_modified = pywt.idwt2(coeffs2_modified, 'haar')
    y_channel_modified = np.clip(y_channel_modified, 0, 255)
    y_channel_modified = y_channel_modified.astype(np.uint8)  # uint8로 변환

    # YCbCr 채널 결합 후 최종 이미지 복원
    modified_ycbcr_image = cv2.merge([y_channel_modified, cb_channel, cr_channel])
    reconstructed_image = cv2.cvtColor(modified_ycbcr_image, cv2.COLOR_YCrCb2BGR)

    # 이미지를 인코딩하여 반환
    success, encoded_image = cv2.imencode('.png', reconstructed_image)
    if success:
        return True, encoded_image
    else:
        return False, None

