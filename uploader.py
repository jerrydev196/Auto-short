import os
import shutil
import random
import ffmpeg
import subprocess

import json

def extract_cover_with_watermark(folder_path, watermark_image):
    video_file = os.path.join(folder_path, 'final-1.mp4')
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

# 上传视频到Bilibili的函数
def upload_video_to_bilibili(tid: int, title: str, desc: str, tag: str, no_reprint: int, video_file: str, cover: str):
    """
    函数用于通过biliup工具上传视频到B站。

    :param tid: 投稿分区
    :param title: 视频标题
    :param desc: 视频简介
    :param tag: 视频标签
    :param no_reprint: 是否禁止转载，0-允许转载，1-禁止转载
    :param video_file: 视频文件路径
    :param cover: 视频封面
    """
    command = [
        "./biliup", "upload", "--tid", str(tid), "--title", title, "--desc", desc,
        "--tag", tag, "--cover", cover, "--no-reprint", str(no_reprint), 
        "--copyright", "1", video_file
    ]
    print(command)
    print("Executing command:", " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Upload successful.")
    else:
        print("Error in uploading video:", result.stderr)

    return result


if __name__ == "__main__":
    tasks_folder = 'storage/tasks'
    watermark_image = 'watermark.png'  # 替换为你的水印图片路径
    
    for task_name in os.listdir(tasks_folder):
        task_folder = os.path.join(tasks_folder, task_name)
        
        # 生成带水印的封面
        
        extract_cover_with_watermark(task_folder, watermark_image)
        cover = os.path.join(task_folder, 'cover_with_watermark.jpg')
        video_file= os.path.join(task_folder, 'final-1.mp4')
        # 传入所有必须的参数值
        tid = 138  # 投稿分区ID，注意这里应为整型，而不是字符串
        title = '胖宝宝语录'
        desc = '胖宝宝语录'
        tag = '搞笑'
        no_reprint = 1  # 禁止转载标记，整型


        # 上传 final-1.mp4 和封面到 BiliBili

        result = upload_video_to_bilibili(tid, title, desc, tag, no_reprint, video_file, cover)
        print(result)

        # 成功上传后删除任务文件夹
        shutil.rmtree(task_folder)
