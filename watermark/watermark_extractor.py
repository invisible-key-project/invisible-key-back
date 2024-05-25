import numpy as np
import pywt
import cv2
import sys
sys.path.append("/opt/homebrew/opt/zbar/lib/python3.11/site-packages")
from pyzbar.pyzbar import decode



def extract_watermark(image_path):
    watermarked_image = cv2.imread(image_path)
    yuv_image = cv2.cvtColor(watermarked_image, cv2.COLOR_BGR2YUV)
    y_channel, u_channel, v_channel = cv2.split(yuv_image)
    coeffs = pywt.dwt2(y_channel, 'haar')
    LL, (LH, HL, HH) = coeffs

    # 2차원 DCT를 적용할 블록의 크기를 정의 (예: 8x8)
    block_size = 8

    watermark = []
    index = 0
    for i in range(0, HL.shape[0], block_size):
        for j in range(0, HL.shape[1], block_size):
            if index > 4095: break;
            block = HL[i:i + block_size, j:j + block_size].astype(np.float32)

            # 실제 블록 크기 확인
            actual_block_size = block.shape
            if actual_block_size == (block_size, block_size):
                # 2차원 DCT 적용
                dct_block = cv2.dct(block)

                # 워터마킹 추출 과정
                C_f = dct_block[1, 0]
                C_r = dct_block[0, 1]

                if (C_f > C_r):
                    watermark.append(1)
                else:
                    watermark.append(0)
            else:
                # 크기가 (8, 8)이 아닌 블록은 변환 없이 그대로 유지
                continue
            index += 1

    # 결과 표시
    extracted_watermark = np.array(watermark, dtype=np.uint8) * 255  # 이진값을 0 또는 255로 변환
    extract_watermark = extracted_watermark.reshape((64, 64))
    _, buffer = cv2.imencode('.jpg', extract_watermark)

    #QRCode 인식하기
    decoded = decode(extract_watermark)

    if decoded:
        # 링크 가져와서 브라우저 실행하기
        decoded_data = decoded[0].data.decode('utf-8')
        print("=========== 인식 성공 ===========")
        print("데이터: ", decoded_data)

    else:
        print("QR 코드를 찾을 수 없습니다.")
        decoded_data = "QR 코드를 찾을 수 없습니다."

    return buffer, decoded_data
