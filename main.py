from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
import os
os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"
from google.cloud import firestore
from google.cloud import storage
from flask import current_app
import logging


def cal_video_length(video_path):
    video = VideoFileClip(video_path)
    print(f"Video duration: {video.duration}")
    return int(video.duration)


def split_video(video_path, chunk_length=10):
    video_length = cal_video_length(video_path)
    chunks = []
    for start in range(0, video_length, chunk_length):
        end = min(start + chunk_length, video_length)
        chunks.append((start, end))
    current_app.logger.info(f"Split video into {len(chunks)} chunks")
    return chunks

if __name__ == "__main__":
    video_path = './test.mp4'
    split_video(video_path)