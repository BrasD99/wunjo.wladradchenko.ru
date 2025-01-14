import os
import cv2
import torch
import numpy as np


def save_empty_mask(num_frame, width, height, mask_save_path, filename_pattern):
    white_mask = 255 * np.ones((height, width, 3), dtype=np.uint8)
    save_path = os.path.join(mask_save_path, filename_pattern % num_frame)
    cv2.imwrite(save_path, white_mask)


def save_video_frames_cv2(video_path, frame_save_path, filename_pattern, resolution_vram_func=None, device="cuda"):
    os.makedirs(frame_save_path, exist_ok=True)
    video_stream = cv2.VideoCapture(video_path)
    width = int(video_stream.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width > height:
        resolution = width
    else:
        resolution = height
    if resolution_vram_func is not None:
        resolution = resolution_vram_func(resolution, device)
    fps = video_stream.get(cv2.CAP_PROP_FPS)

    num_frame = 1
    while True:
        success, frame = video_stream.read()
        if not success:
            break  # exit the loop if no more frames are available
        if resolution_vram_func is not None:
            frame = resize_frame(frame, resolution)
            height, width, _ = frame.shape
        cv2.imwrite(os.path.join(frame_save_path, filename_pattern % num_frame), frame)
        num_frame += 1
    video_stream.release()
    return fps, num_frame, width, height


def save_image_frame_cv2(image_path, save_path, filename_pattern, resolution_vram_func=None, device="cuda"):
    os.makedirs(save_path, exist_ok=True)
    frame = cv2.imread(image_path)
    width = frame.shape[1]
    height = frame.shape[0]
    if width > height:
        resolution = width
    else:
        resolution = height
    if resolution_vram_func is not None:
        resolution = resolution_vram_func(resolution, device)
    if resolution_vram_func is not None:
        frame = resize_frame(frame, resolution)
        height, width, _ = frame.shape
    cv2.imwrite(os.path.join(save_path, filename_pattern % 1), frame)
    return 0, 1, width, height


def resize_frame(frame, resolution):
    H, W, C = frame.shape
    H = float(H)
    W = float(W)
    aspect_ratio = W / H
    k = float(resolution) / min(H, W)
    H *= k
    W *= k
    if H < W:
        W = resolution
        H = int(resolution / aspect_ratio)
    else:
        H = resolution
        W = int(aspect_ratio * resolution)
    H = int(np.round(H / 64.0)) * 64
    W = int(np.round(W / 64.0)) * 64
    resized_frame = cv2.resize(frame, (W, H), interpolation=cv2.INTER_LANCZOS4 if k > 1 else cv2.INTER_AREA)
    return resized_frame


def vram_limit_device_resolution_diffusion(resolution, device="cuda"):
    # get max limit target size
    gpu_vram = torch.cuda.get_device_properties(device).total_memory / (1024 ** 3)
    # table of gpu memory limit
    gpu_table = {24: 1280, 18: 1024, 14: 768, 10: 640, 8: 576, 7: 512, 6: 448, 5: 320, 4: 192, 0: 0}
    # get user resize for gpu
    device_resolution = max(val for key, val in gpu_table.items() if key <= gpu_vram)
    print(f"Limit VRAM is {gpu_vram} Gb and size {device_resolution}.")
    if gpu_vram < 4:
        print(f"Small VRAM to use GPU. Will be use config resolution")
    if resolution < device_resolution:
        print(f"Video will not resize")
        return resolution
    return device_resolution
