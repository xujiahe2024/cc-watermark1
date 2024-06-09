from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
import os
from google.cloud import firestore
from google.cloud import storage
import logging
import time

Storage = storage.Client()
database = firestore.Client()

output_dir = os.path.abspath('./output')

def cal_video_length(video_path):
    video = VideoFileClip(video_path)
    return int(video.duration)


def split_video(video_path, chunk_length=10):
    video_length = cal_video_length(video_path)
    chunks = []
    for start in range(0, video_length, chunk_length):
        end = min(start + chunk_length, video_length)
        chunks.append((start, end))
    return chunks
    

def process_chunk(job_id, video_url, start, end, current_chunk, total_chunks):
        global Storage
        global database
        start_time = time.time()
        #logging.info(f"Processing chunk {current_chunk} of {total_chunks} for job {job_id}")
        database = firestore.Client()
        job_ref = database.collection('job').document(job_id)
        
        video_path = f'{output_dir}/{job_id}_video_{current_chunk}.webm'
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        right_video_url = f'videos/{job_id}_{current_chunk}.webm'
        #video_path = f'{tmpdir}/{job_id}_video_{current_chunk}.webm'
        #f'videos/{job_id}_{i}.webm'
        print(output_dir)
        
        if not os.path.exists(video_path):
            blob = Storage.bucket('ccmarkbucket').blob(right_video_url)
            blob.download_to_filename(video_path)
            
        watermark_path = f'{output_dir}/{job_id}_watermark_{time.time()}.png'
        #watermark_path = os.path.join(output_dir, f'{job_id}_watermark.png')
        
        blob = Storage.bucket('ccmarkbucket').blob(f'watermarks/{job_id}.png')
        blob.download_to_filename(watermark_path)
        
        print("watermark_path: ", watermark_path)
            
        #logging.info(f"Downloaded video for job {job_id}")
        
        download_time = time.time()
        
        video = VideoFileClip(video_path)

        #video.duration = 10
        #video = VideoFileClip(video_path).subclip(start, end)
        watermark = ImageClip(watermark_path).set_duration(video.duration)
        watermark = watermark.resize(height=50).margin(right=8, bottom=8, opacity=0).set_position(("right", "bottom"))

        processed = CompositeVideoClip([video, watermark])
        
        process_time = time.time()
        
        os.remove(video_path)
        os.remove(watermark_path)
        
        chunk_path = f'{output_dir}/{job_id}_final_chunk{current_chunk}.webm'
        processed.write_videofile(chunk_path, logger=None)
        
        
        
        logging.info(f"Processed chunk {current_chunk} of {total_chunks} for job {job_id}")

        bucket = Storage.bucket('ccmarkbucket')
        blob = bucket.blob(f'{output_dir}/{job_id}_final_chunk{current_chunk}.webm')
        blob.upload_from_filename(chunk_path)
        
        #delete chunk file
        os.remove(chunk_path)
        
        process_time = time.time()

        logging.info(f"Uploaded chunk {current_chunk} of {total_chunks} for job {job_id}")
        #job_data = job_ref.get().to_dict()
        #logging.info(f"Job data1: {job_data}")
        
        job_ref.update({'completed_chunks': firestore.Increment(1)})
        job_ref.set({f'task_{current_chunk}':{
            'download_time': download_time - start_time,
            'process_time': process_time - download_time,
            'upload_time': time.time() - process_time
            }}, merge=True)


        job_data = job_ref.get().to_dict()
        logging.info(f"Job data2: {job_data}")
        if job_data['completed_chunks'] >= job_data['total_chunks']:
            logging.info(f"All chunks processed for job {job_id}")
            #merge_chunks(job_id)
            #job_ref.update({'status': 'completed', 'progress': 100})



def merge_chunks(job_id):
    database = firestore.Client()
    job_ref = database.collection('job').document(job_id)
    job_data = job_ref.get().to_dict()
    logging.info(f"Job data3: {job_data}")
    chunks_path = [f'{output_dir}/{job_id}_final_chunk{current_chunk}.webm' for current_chunk in range(job_data['total_chunks'])]
    logging.info(f"chunks_path: {chunks_path}")
    clips = [VideoFileClip(chunk) for chunk in chunks_path]
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(f'{output_dir}/final_{job_id}.mp4')
    final_result_path = f'{output_dir}/final_{job_id}.mp4'

    bucket = Storage.bucket('ccmarkbucket')
    final_blob = bucket.blob(f'{output_dir}/{job_id}_final.mp4')
    final_blob.upload_from_filename(final_result_path)
    logging.info(f"Uploaded final result for job {job_id}")




# def merge_chunks(job_id, chunks_path, storage, database):
#     job_ref = database.collection('job').document(job_id)

#     clips = [VideoFileClip(path) for path in chunks_path]
#     final_clip = concatenate_videoclips(clips)

#     final_result_path = f'{output_dir}/final_{job_id}.webm'
#     final_clip.write_videofile(final_result_path, codec='libx264')

#     bucket = storage.bucket('ccmarkbucket')
#     final_blob = bucket.blob(f'{output_dir}/{job_id}_final.webm')
#     final_blob.upload_from_filename(final_result_path)

#     job_ref.update({'status': 'completed', 'progress': 100, 'resulturl': final_blob.public_url})


# def processor(job_id, video_path, watermark_path, storage, database):
#     chunks = split_video(video_path, chunk_length=10)
#     total_chunks = len(chunks)
#     for i, (start, end) in enumerate(chunks):
#         process_chunk(job_id, video_path, watermark_path, start, end, i + 1, total_chunks, storage, database)

#     chunks_path = [f'{output_dir}/{job_id}_chunk{i+1}.webm' for i in range(total_chunks)]

#     merge_chunks(job_id, chunks_path, storage, database)

    









   
  
