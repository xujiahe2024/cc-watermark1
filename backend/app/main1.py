from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
import os
import logging
import threading
import time

from google.cloud import storage, firestore, pubsub_v1
import concurrent.futures
try:
    from worker2 import split_video
    import message_queue1
    import uuid
    import json
except Exception as e:
    print(f"An error occurred while importing modules: {e}")
    
    
# Create a lock
merge_lock = threading.Lock()

output_dir = os.path.abspath('./output')

storage = storage.Client()
database = firestore.Client()


class MyFlaskApp(Flask):
    def __init__(self, *args, **kwargs):
        super(MyFlaskApp, self).__init__(*args, **kwargs)


app = MyFlaskApp(__name__)
app.logger.setLevel(logging.INFO)
app.app_context().push()


CORS(app, resources={r"/*": {"origins": "http://34.91.227.196"}})
bucketname = 'ccmarkbucket'
publisher = pubsub_v1.PublisherClient()
#topic_name = 'projects/watermarking-424614/topics/image-watermark-sub'


#parallel downloading of chunks
def download_chunk(chunk, chunk_path_web):
    chunk_blob = storage.bucket(bucketname).blob(chunk_path_web)
    chunk_blob.download_to_filename(chunk)
    

#parallel preclip into chunks
def clip_chunk(i, start_end, full_video, job_id, bucket):
    start, end = start_end
    video = full_video.subclip(start, end)
    video.write_videofile(f'{output_dir}/{job_id}_chunk{i}.webm', codec = "libvpx", logger = None)
    blob = bucket.blob(f'videos/{job_id}_{i}.webm')
    blob.upload_from_filename(f'{output_dir}/{job_id}_chunk{i}.webm')
    os.remove(f'{output_dir}/{job_id}_chunk{i}.webm')


@app.route('/upload', methods=['POST'])
def upload():
    try:
        app.logger.info('form: %s', request.form)
        videofile = request.files.get('Videofile')
        videourl = request.form.get('Videourl')
        isFaas = request.form.get('IsFaas')
        markimage = request.files.get('Watermarkimage')
        app.logger.info('isFaas: ' + isFaas)
        for key, value in request.form.items():
            app.logger.info(f"Key: {key}, Value: {value}")

        if not (videofile or videourl) or not markimage:
            return jsonify({'You have to upload video and markimage'}), 400
        
        job_id = str(uuid.uuid4())
        #job_id = str("4b87c71e-764f-4f25-a8f3-ae86fbdf9249")
        
        
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件路径
        video_path = os.path.join(output_dir, f'{job_id}_video.webm')
        watermark_path = os.path.join(output_dir, f'{job_id}_watermark.png')

        #video_path = f'/tmp/{job_id}_video.webm'
        #watermark_path = f'/tmp/{job_id}_watermark.png'
        
        start_time = time.time()

        if videofile:
            videofile.save(video_path)
        else:
            os.system(f'wget -O {video_path} {videourl}')

        markimage.save(watermark_path)
        
        storetime = time.time()
        app.logger.info(f"Time taken to store files: {storetime - start_time}")

        bucket = storage.bucket(bucketname)
        #blob = bucket.blob(f'videos/{job_id}.webm')
        #blob.upload_from_filename(video_path)
        
        video_url = f'videos/{job_id}.webm'
        
        blob = bucket.blob(f'watermarks/{job_id}.png')
        blob.upload_from_filename(watermark_path)
        
        uploadtime = time.time()
        app.logger.info(f"Time taken to upload files: {uploadtime - storetime}")

        #processor(job_id, video_path, watermark_path, storage, database)
      

        chunks = split_video(video_path, chunk_length=0.05)
        chunks = chunks[:-1]
        
        job_ref = database.collection('job').document(job_id)
        job_ref.set({
            'status': 'pending',
            'progress': 0,
            'completed_chunks': 0,
            'total_chunks': len(chunks), 
            'resulturl': None
        })
        
        full_video = VideoFileClip(video_path)
        
        """
        for i, (start, end) in enumerate(chunks):
            video = full_video.subclip(start, end)
            video.write_videofile(f'{output_dir}/{job_id}_chunk{i}.webm', codec = "libvpx", logger = None)
            blob = bucket.blob(f'videos/{job_id}_{i}.webm')
            blob.upload_from_filename(f'{output_dir}/{job_id}_chunk{i}.webm')
            #process_chunk(job_id, video_path, watermark_path, start, end, i + 1, len(chunks), video_url)
        """
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(clip_chunk, range(len(chunks)), chunks, [full_video]*len(chunks), [job_id]*len(chunks), [bucket]*len(chunks))
        
        splittime = time.time()
        app.logger.info(f"Time taken to split video: {splittime - uploadtime}")
        
        #with concurrent.futures.ThreadPoolExecutor() as executor:
        #    executor.map(message_queue1.publish_message, [job_id]*len(chunks), [isFaas]*len(chunks), [watermark_path]*len(chunks), chunks, [video_url]*len(chunks), range(len(chunks)), [len(chunks)]*len(chunks))
        message_queue1.publish_messages(job_id, False, watermark_path, chunks, video_url)

        publishtime = time.time()
        app.logger.info(f"Time taken to publish messages: {publishtime - splittime}")

        job_ref.update({'storage_time': storetime - start_time, 'upload_time': uploadtime - storetime, 'split_time': splittime - uploadtime, 'publish_time': publishtime - splittime, 'total_time': publishtime - start_time})
        
        return jsonify({'Jobid': job_id, 'message': 'Your video is processing 3'})
    
    except Exception as e:
        app.logger.error('Failed to process upload', exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/upload_to_faas', methods=['POST'])
def upload_to_faas():
    try:
        
        app.logger.info('form: %s', request.form)
        videofile = request.files.get('Videofile')
        videourl = request.form.get('Videourl')
        isFaas = request.form.get('IsFaas')
        markimage = request.files.get('Watermarkimage')
        app.logger.info('isFaas: ' + isFaas)
        for key, value in request.form.items():
            app.logger.info(f"Key: {key}, Value: {value}")

        if not (videofile or videourl) or not markimage:
            return jsonify({'You have to upload video and markimage'}), 400
        
        job_id = str(uuid.uuid4())
        #job_id = str("4b87c71e-764f-4f25-a8f3-ae86fbdf9249")
        
        
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件路径
        video_path = os.path.join(output_dir, f'{job_id}_video.webm')
        watermark_path = os.path.join(output_dir, f'{job_id}_watermark.png')

        #video_path = f'/tmp/{job_id}_video.webm'
        #watermark_path = f'/tmp/{job_id}_watermark.png'
        
        start_time = time.time()

        if videofile:
            videofile.save(video_path)
        else:
            os.system(f'wget -O {video_path} {videourl}')

        markimage.save(watermark_path)
        
        storetime = time.time()
        app.logger.info(f"Time taken to store files: {storetime - start_time}")

        bucket = storage.bucket(bucketname)
        #blob = bucket.blob(f'videos/{job_id}.webm')
        #blob.upload_from_filename(video_path)
        
        video_url = f'videos/{job_id}.webm'
        
        blob = bucket.blob(f'watermarks/{job_id}.png')
        blob.upload_from_filename(watermark_path)
        
        uploadtime = time.time()
        app.logger.info(f"Time taken to upload files: {uploadtime - storetime}")

        #processor(job_id, video_path, watermark_path, storage, database)
      

        chunks = split_video(video_path, chunk_length=0.05)
        chunks = chunks[:-1]
        
        job_ref = database.collection('job').document(job_id)
        job_ref.set({
            'status': 'pending',
            'progress': 0,
            'completed_chunks': 0,
            'total_chunks': len(chunks), 
            'resulturl': None
        })
        
        full_video = VideoFileClip(video_path)
        
        """
        for i, (start, end) in enumerate(chunks):
            video = full_video.subclip(start, end)
            video.write_videofile(f'{output_dir}/{job_id}_chunk{i}.webm', codec = "libvpx", logger = None)
            blob = bucket.blob(f'videos/{job_id}_{i}.webm')
            blob.upload_from_filename(f'{output_dir}/{job_id}_chunk{i}.webm')
            #process_chunk(job_id, video_path, watermark_path, start, end, i + 1, len(chunks), video_url)
        """
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(clip_chunk, range(len(chunks)), chunks, [full_video]*len(chunks), [job_id]*len(chunks), [bucket]*len(chunks))
        
        splittime = time.time()
        app.logger.info(f"Time taken to split video: {splittime - uploadtime}")
        
        #with concurrent.futures.ThreadPoolExecutor() as executor:
        #    executor.map(message_queue1.publish_message, [job_id]*len(chunks), [isFaas]*len(chunks), [watermark_path]*len(chunks), chunks, [video_url]*len(chunks), range(len(chunks)), [len(chunks)]*len(chunks))
        message_queue1.publish_messages(job_id, True, watermark_path, chunks, video_url)

        publishtime = time.time()
        app.logger.info(f"Time taken to publish messages: {publishtime - splittime}")

        job_ref.update({'storage_time': storetime - start_time, 'upload_time': uploadtime - storetime, 'split_time': splittime - uploadtime, 'publish_time': publishtime - splittime, 'total_time': publishtime - start_time})
        
        return jsonify({'Jobid': job_id, 'message': 'Your video is processing 3'})
    
    except Exception as e:
        app.logger.error('Failed to process upload', exc_info=True)
        return jsonify({'error': str(e)}), 500




@app.route('/status', methods=['GET'])
def status():
    try:
        job_id = request.args.get('Jobid')
        if not job_id:
            return jsonify({'error': 'Job ID is required.'}), 400
    
        job_ref = database.collection('job').document(job_id)
        job = job_ref.get()
        if not job.exists:
            return jsonify({'error': 'There is no job.'}), 404
        job_data = job.to_dict()
        if job_data['completed_chunks'] >= job_data['total_chunks'] and job_data['status'] != 'completed':
            if merge_lock.acquire(blocking=False):
                merge_chunks(job_id)
                merge_lock.release()
                job_ref = database.collection('job').document(job_id)
                job = job_ref.get()
        job_data = job.to_dict()
        return jsonify(job_data)
    except Exception as e:
        app.logger.error('Failed to get status', exc_info=True)
        return jsonify({'error': str(e)}), 500
    


def merge_chunks(job_id):
    global database
    global storage
    job_ref = database.collection('job').document(job_id)
    job_data = job_ref.get().to_dict()
    #print(f"Job data3: {job_data}")
    chunks_path_web = [f'final/{job_id}_final_chunk{current_chunk}.webm' for current_chunk in range(job_data['total_chunks'])]
    chunks_path = [f'{output_dir}/{job_id}_final_chunk{current_chunk}.webm' for current_chunk in range(job_data['total_chunks'])]
    #print(f"chunks_path: {chunks_path}")
    
    for i, chunk in enumerate(chunks_path):
        chunk_blob = storage.bucket(bucketname).blob(chunks_path_web[i])
        chunk_blob.download_to_filename(chunk)
    """
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(download_chunk, chunks_path, chunks_path_web)
    """
        
    clips = [VideoFileClip(chunk) for chunk in chunks_path]
    final_clip = concatenate_videoclips(clips)
    #tmpfilePath = f'{tmpdir}/{job_id}_final_temp_audiofile_path'
    final_clip.upload_video(f'{output_dir}/final_{job_id}.mp4', codec = "libvpx", logger = None)
    final_clip.write_videofile(f'{output_dir}/final_{job_id}.mp4', temp_audiofile_path = output_dir, logger = None)
    final_result_path = f'{output_dir}/final_{job_id}.mp4'

    bucket = storage.bucket('ccmarkbucket')
    final_blob = bucket.blob(f'{output_dir}/{job_id}_final.mp4')
    final_blob.upload_from_filename(final_result_path)
    
    os.remove(final_result_path)
    for chunk in chunks_path:
        os.remove(chunk)
    
    job_ref.update({'status': 'completed', 'progress': 100, 'resulturl': final_blob.public_url})
    
    #print(f"Uploaded final result for job {job_id}")


    

@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello World!'}), 200


@app.route('/download', methods=['GET'])
def download():
    job_id = request.args.get('Jobid')
    if not job_id:
        return jsonify({'error': 'Job ID is required.'}), 400

    job_ref = database.collection('job').document(job_id)
    job = job_ref.get()
    if not job.exists:
        return jsonify({'error': 'There is no job.'}), 404

    job_data = job.to_dict()
    if job_data['status'] != 'completed':
        return jsonify({'error': 'Job is not completed.'}), 400
    
    bucket = storage.bucket(bucketname)
    blob = bucket.blob(f'{output_dir}/{job_id}_final.mp4')
    blob.download_to_filename(f'{output_dir}/final_{job_id}.mp4')

    return send_file(f'{output_dir}/final_{job_id}.mp4')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
