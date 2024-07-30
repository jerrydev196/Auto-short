import os
import shutil
import random
import ffmpeg
from biliup.plugins.bili_webup import BiliBili, Data

import json

def extract_login_data(file_path):
    file_path = "biliup/cookies.json"  # 替换为实际存储凭据的文件路径
    login_data = extract_login_data(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extracting necessary information from the JSON structure
    cookies = data.get("cookie_info", {}).get("cookies", [])
    access_token = data.get("token_info", {}).get("access_token", "")
    
    # Constructing the login data dictionary
    login_data = {
        'cookies': {
            'SESSDATA': next((cookie['value'] for cookie in cookies if cookie['name'] == 'SESSDATA'), ''),
            'bili_jct': next((cookie['value'] for cookie in cookies if cookie['name'] == 'bili_jct'), ''),
            'DedeUserID__ckMd5': next((cookie['value'] for cookie in cookies if cookie['name'] == 'DedeUserID__ckMd5'), ''),
            'DedeUserID': next((cookie['value'] for cookie in cookies if cookie['name'] == 'DedeUserID'), '')
        },
        'access_token': access_token
    }
    
    return login_data


def extract_cover_with_watermark(folder_path, watermark_image):
    video_file = os.path.join(folder_path, 'combined-1.mp4')
    output_file = os.path.join(folder_path, 'cover_with_watermark.jpg')
    
    # 获取视频的持续时间
    probe = ffmpeg.probe(video_file)
    duration = float(probe['format']['duration'])
    
    # 在视频持续时间范围内随机选择一个时间点
    random_time = random.uniform(0, duration)
    
    # 提取所选时间点的帧
    (
        ffmpeg
        .input(video_file, ss=random_time)
        .output(output_file, vframes=1)
        .overwrite_output()
        .run()
    )
    
    # 将水印图片作为 FilterableStream 加载
    watermark = ffmpeg.input(watermark_image)
    
    # 获取提取帧的尺寸信息
    frame_info = ffmpeg.probe(output_file, show_entries='stream=width,height')
    frame_width = int(frame_info['streams'][0]['width'])
    frame_height = int(frame_info['streams'][0]['height'])
    
    # 获取水印图片的尺寸信息
    watermark_info = ffmpeg.probe(watermark_image, show_entries='stream=width,height')
    watermark_width = int(watermark_info['streams'][0]['width'])
    watermark_height = int(watermark_info['streams'][0]['height'])
    
    # 计算水印在左下角的位置
    x_position = 10  # 水平位置，根据需要调整
    y_position = (frame_height // 2) - (watermark_height // 2)  # 垂直居中
    
    # 将水印添加到提取的帧上
    (
        ffmpeg
        .input(output_file)
        .overlay(watermark, x=x_position, y=y_position)
        .output(os.path.join(folder_path, 'cover_with_watermark.jpg'))
        .overwrite_output()
        .run()
    )
    
    print(f"从 {video_file} 在 {random_time} 秒时提取带水印的封面到 {output_file}")

def upload_video_to_bilibili(mp4_file, cover_file):
    # 替换为你的 BiliBili 上传逻辑
    print(f"上传视频: {mp4_file}")
    with BiliBili() as bili:
        bili.login("bili.cookie", login_data)
        video_part = bili.upload_file(mp4_file)  # 上传视频
        video_cover = bili.cover_up(cover_file).replace('http:', '')  # 上传封面
        # 根据需要添加更多与 BiliBili API 交互的逻辑
        # 假设有像 `bili.append(video_part)`、`bili.submit()` 等方法
    print(f"成功上传视频: {mp4_file}")

if __name__ == "__main__":
    tasks_folder = 'storage/tasks'
    watermark_image = 'watermark.png'  # 替换为你的水印图片路径
    
    for task_name in os.listdir(tasks_folder):
        task_folder = os.path.join(tasks_folder, task_name)
        
        # 生成带水印的封面
        cover_file = os.path.join(task_folder, 'cover_with_watermark.jpg')
        extract_cover_with_watermark(task_folder, watermark_image)
        
        # 上传 final-1.mp4 和封面到 BiliBili
        final_mp4_file = os.path.join(task_folder, 'final-1.mp4')
        upload_video_to_bilibili(final_mp4_file, cover_file)
        
        # 成功上传后删除任务文件夹
        shutil.rmtree(task_folder)
