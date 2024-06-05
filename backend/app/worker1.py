from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

def processor(job_id, video_path, watermark_path, storage, database):
    job_ref = database.collection('job').document(job_id)
    
    video = VideoFileClip(video_path)
    print(video.rotation, video.size)

    watermark = ImageClip(watermark_path).set_duration(video.duration)
    
    watermark = watermark.resize(height=50).margin(right=8, bottom=8, opacity=0).set_position(("right", "bottom"))
    
    
    processed = CompositeVideoClip([video, watermark])
    result_path = f'tmp/{job_id}_result.mp4'
    processed.write_videofile(result_path, codec='libx264')

    bucket = storage.bucket('ccmarkbucket')
    blob = bucket.blob(f'results/{job_id}.mp4')
    blob.upload_from_filename(result_path)

    resulturl = blob.public_url

    job_ref.update({
        'status': 'completed',
        'progress': 100,
        'resulturl': resulturl
    })