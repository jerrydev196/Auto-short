import os
import random
import ffmpeg

def extract_cover_with_watermark(folder_path, watermark_image):
    video_file = os.path.join(folder_path, 'combined-1.mp4')
    output_file = os.path.join(folder_path, 'cover_with_watermark.jpg')
    
    # Get duration of the video
    probe = ffmpeg.probe(video_file)
    duration = float(probe['format']['duration'])
    
    # Choose a random time within the duration
    random_time = random.uniform(0, duration)
    
    # Extract frame at the chosen time
    (
        ffmpeg
        .input(video_file, ss=random_time)
        .output(output_file, vframes=1)
        .overwrite_output()
        .run()
    )
    
    # Load watermark image as FilterableStream
    watermark = ffmpeg.input(watermark_image)
    
    # Get dimensions of the extracted frame
    frame_info = ffmpeg.probe(output_file, show_entries='stream=width,height')
    frame_width = int(frame_info['streams'][0]['width'])
    frame_height = int(frame_info['streams'][0]['height'])
    
    # Get dimensions of the watermark image
    watermark_info = ffmpeg.probe(watermark_image, show_entries='stream=width,height')
    watermark_width = int(watermark_info['streams'][0]['width'])
    watermark_height = int(watermark_info['streams'][0]['height'])
    
    # Calculate position for watermark in the middle-left part
    x_position = 10  # Adjust as needed for horizontal position
    y_position = (frame_height // 2) - (watermark_height // 2)  # Center vertically
    
    # Add watermark to the extracted frame
    (
        ffmpeg
        .input(output_file)
        .overlay(watermark, x=x_position, y=y_position)
        .output(os.path.join(folder_path, 'cover_with_watermark.jpg'))
        .overwrite_output()
        .run()
    )
    
    print(f"Extracted cover with watermark from {video_file} at {random_time} seconds to {output_file}")

# Example usage:
folder_path = 'storage/tasks/d91ba5f8-a472-4189-8d72-53f7c8d7e5b3'
watermark_image = 'watermark.png'  # Replace with your watermark image path
extract_cover_with_watermark(folder_path, watermark_image)
