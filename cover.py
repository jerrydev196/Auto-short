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
    
    # Add watermark to the extracted frame
    (
        ffmpeg
        .input(output_file)
        .overlay(watermark, x=10, y='main_h-overlay_h-10')
        .output(os.path.join(folder_path, 'cover_with_watermark.jpg'))
        .overwrite_output()
        .run()
    )
    
    print(f"Extracted cover with watermark from {video_file} at {random_time} seconds to {output_file}")

# Example usage:
folder_path = 'storage/tasks/d91ba5f8-a472-4189-8d72-53f7c8d7e5b3'
watermark_image = 'watermark.png'  # Replace with your watermark image path
extract_cover_with_watermark(folder_path, watermark_image)