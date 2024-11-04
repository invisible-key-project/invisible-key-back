import numpy as np
import pywt
import cv2
import sys
import random
sys.path.append("/opt/homebrew/opt/zbar/lib/python3.11/site-packages")
from pyzbar.pyzbar import decode

def extract_watermark(image_path):
    watermarked_image = cv2.imread(image_path)
    ycbcr_image = cv2.cvtColor(watermarked_image, cv2.COLOR_BGR2YCrCb)
    y_channel, cb_channel, cr_channel = cv2.split(ycbcr_image)

    # Y채널에 DWT 적용하여 LH 대역 추출
    coeffs2 = pywt.dwt2(y_channel, 'haar')
    LL, (LH, HL, HH) = coeffs2  # Y채널을 DWT하여 LH 대역 추출

    block_size = 8

    # 랜덤 블록 선택을 위해 난수 생성기 초기화
    random_seed = 42
    random.seed(random_seed)

    block_positions = [(i, j) for i in range(0, LH.shape[0], block_size) for j in range(0, LH.shape[1], block_size)]
    random.shuffle(block_positions)

    extracted_key = []
    index = 0

    for pos in block_positions:
        if index >= 4096:  # 워터마크 크기에 맞춰 제한
            break

        i, j = pos
        lh_block = LH[i:i + block_size, j:j + block_size].astype(np.float32)

        if lh_block.shape == (block_size, block_size):
            dct_lh_block = cv2.dct(lh_block)
            C_f = dct_lh_block[0, 1]
            C_r = dct_lh_block[1, 0]

            if C_f > C_r:
                extracted_key.append(255)
            else:
                extracted_key.append(0)
            index += 1

    extracted_key = np.array(extracted_key, dtype=np.uint8)

    # 원래의 IDW와 비교하여 최종 워터마크 추출
    IDW_extracted = []
    index = 0

    for i in range(0, y_channel.shape[0], block_size):
        for j in range(0, y_channel.shape[1], block_size):
            if index >= extracted_key.size:
                break

            y_block = y_channel[i:i + block_size, j:j + block_size].astype(np.float32)
            cb_block = cb_channel[i:i + block_size, j:j + block_size].astype(np.float32)

            if y_block.shape == (block_size, block_size) and cb_block.shape == (block_size, block_size):
                dct_y_block = cv2.dct(y_block)
                dct_cb_block = cv2.dct(cb_block)

                B_y = dct_y_block[0, 0]
                B_cb = dct_cb_block[0, 0]

                if B_y > B_cb:
                    IDW_extracted.append(1)
                else:
                    IDW_extracted.append(0)

            index += 1

    IDW_extracted = np.array(IDW_extracted[:extracted_key.size], dtype=np.uint8)
    extracted_watermark = np.bitwise_xor(IDW_extracted, extracted_key)
    extracted_watermark = np.array([255 if value >= 128 else 0 for value in extracted_watermark])
    extracted_watermark_image = extracted_watermark.reshape(64, 64)

    # QRCode 인식하기
    decoded = decode(extracted_watermark_image)

    if decoded:
        decoded_data = decoded[0].data.decode('utf-8')
        print("=========== 인식 성공 ===========")
        print("데이터: ", decoded_data)
    else:
        print("QR 코드를 찾을 수 없습니다.")
        decoded_data = "QR 코드를 찾을 수 없습니다."

    _, buffer = cv2.imencode('.jpg', extracted_watermark_image)

    return buffer, decoded_data