from flask import Flask, request, jsonify, send_file
from google.cloud import storage, firestore
from worker1 import processor
import os
import uuid
from flask_cors import CORS

output_dir = os.path.abspath('./output')

storage = storage.Client()
database = firestore.Client()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://34.91.227.196"}})
bucketname = 'ccmarkbucket'

@app.route('/upload', methods=['POST'])
def upload():
    try:
        videofile = request.files.get('Videofile')
        videourl = request.form.get('Videourl')
        markimage = request.files.get('Watermarkimage')

        if not (videofile or videourl) or not markimage:
            return jsonify({'You have to upload video and markimage'}), 400
        
        # job_id = str(uuid.uuid4())
        job_id = str("4b87c71e-764f-4f25-a8f3-ae86fbdf9249")
        job_ref = database.collection('job').document(job_id)
        job_ref.set({
            'status': 'pending',
            'progress': 0,
            'resulturl': None
        })
        
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件路径
        video_path = os.path.join(output_dir, f'{job_id}_video.mp4')
        watermark_path = os.path.join(output_dir, f'{job_id}_watermark.png')

        #video_path = f'/tmp/{job_id}_video.mp4'
        #watermark_path = f'/tmp/{job_id}_watermark.png'
        
        

        if videofile:
            videofile.save(video_path)
        else:
            os.system(f'wget -O {video_path} {videourl}')

        markimage.save(watermark_path)

        bucket = storage.bucket(bucketname)
        blob = bucket.blob(f'videos/{job_id}.mp4')
        blob.upload_from_filename(video_path)
        blob = bucket.blob(f'watermarks/{job_id}.png')
        blob.upload_from_filename(watermark_path)

        processor(job_id, video_path, watermark_path, storage, database)

        return jsonify({'Jobid': job_id})
    
    except Exception as e:
        app.logger.error('Failed to process upload', exc_info=True)
        return jsonify({'error': str(e)}), 500



@app.route('/status', methods=['GET'])
def status():
    job_id = request.args.get('Jobid')
    if not job_id:
        return jsonify({'error': 'Job ID is required.'}), 400
    
    job_ref = database.collection('job').document(job_id)
    job = job_ref.get()
    if not job.exists:
        return jsonify({'error': 'There is no job.'}), 404

    return jsonify(job.to_dict())

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
    blob = bucket.blob(f'results/{job_id}.mp4')
    blob.download_to_filename(f'{output_dir}/finished_{job_id}.mp4')

    return send_file(f'{output_dir}/finished_{job_id}.mp4')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
