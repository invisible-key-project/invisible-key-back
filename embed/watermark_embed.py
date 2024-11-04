import qrcode
from PIL import Image
import numpy as np
import cv2
import pywt
import random

def apply_watermark(original_image, watermark_image):

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

    # 원본 이미지와 워터마크 이미지를 numpy 배열로 변환
    original_image = cv2.cvtColor(np.array(original_image), cv2.COLOR_RGB2BGR)
    watermark_image = cv2.cvtColor(np.array(watermark_image), cv2.COLOR_RGB2GRAY)

    # 이미지 크기 조정 (홀수일 경우 1픽셀 제거)
    def adjust_image_size(image):
        height, width = image.shape[:2]
        if height % 2 != 0:
            height -= 1
        if width % 2 != 0:
            width -= 1
        return cv2.resize(image, (width, height))

    original_image = adjust_image_size(original_image)

    # YCbCr로 변환하여 채널 분리
    ycbcr_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2YCrCb)
    y_channel, cb_channel, cr_channel = cv2.split(ycbcr_image)

    # Y 채널에 DWT 적용
    coeffs2 = pywt.dwt2(y_channel, 'haar')
    LL, (LH, HL, HH) = coeffs2

    # 워터마크 이미지 이진화
    _, watermark = cv2.threshold(watermark_image, 128, 255, cv2.THRESH_BINARY)
    watermark = watermark.reshape(-1)

    block_size = 8
    index = 0
    IDW = []

    # IDW 배열 생성
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

                if B_y > B_cb:
                    IDW.append(1)
                else:
                    IDW.append(0)
                index += 1

    IDW = np.array(IDW[:watermark.size])
    KEY = np.bitwise_xor(IDW, watermark)
    KEY = np.array([255 if value >= 128 else 0 for value in KEY])

    random_seed = 42
    random.seed(random_seed)
    block_positions = [(i, j) for i in range(0, LH.shape[0], block_size) for j in range(0, LH.shape[1], block_size)]
    random.shuffle(block_positions)

    index = 0
    for pos in block_positions:
        if index >= KEY.size:
            break

        i, j = pos
        lh_block = LH[i:i + block_size, j:j + block_size].astype(np.float32)

        if lh_block.shape == (block_size, block_size):
            dct_lh_block = cv2.dct(lh_block)
            dct_lh_block = embed_watermark(dct_lh_block, KEY, index)
            LH[i:i + block_size, j:j + block_size] = cv2.idct(dct_lh_block)
            index += 1

    coeffs2_modified = (LL, (LH, HL, HH))
    y_channel_modified = pywt.idwt2(coeffs2_modified, 'haar')
    y_channel_modified = np.clip(y_channel_modified, 0, 255).astype(np.uint8)

    reconstructed_image = cv2.merge([y_channel_modified, cb_channel, cr_channel])
    reconstructed_image = cv2.cvtColor(reconstructed_image,  cv2.COLOR_YCrCb2BGR)

    success, encoded_image = cv2.imencode('.png', reconstructed_image)
    if success:
        return True, encoded_image
    else:
        return False, None