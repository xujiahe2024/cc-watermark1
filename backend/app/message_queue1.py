from google.cloud import pubsub_v1
from worker2 import process_chunk
import json
import threading

project_id = "watermarking-424614"
topic_id = "image-watermark-sub"

pub_client = pubsub_v1.PublisherClient()
topic_path = pub_client.topic_path(project_id, topic_id)

"""

def initialize_publisher():
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    def publish_messages():
        for i in range(10):
            data = f"Message number {i}"
            # Data must be a bytestring
            data = data.encode("utf-8")
            # Publish a message
            future = publisher.publish(topic_path, data)
            print(f"Published {data} to {topic_path}: {future.result()}")
            """

    #从某个视频的第start帧操作到第end帧
    # def publish_messages(video_url, start, end):
    #     if video_url and start and end:
    #         # Create a map object
    #         data = {
    #             "video_url": video_url,
    #             "start": start,
    #             "end": end
    #         }
    #         # Convert the map object to a JSON string
    #         data = json.dumps(data)
    #         # Data must be a bytestring
    #         data = data.encode("utf-8")
    #         # Publish a message
    #         future = publisher.publish(topic_path, data)
    #         print(f"Published {data} to {topic_path}: {future.result()}")

def publish_messages(job_id, video_path, watermark_path, chunks, topic_name):
        for i, (start, end) in enumerate(chunks):
            data = json.dumps({
                'job_id': job_id,
                'video_url': video_path,
                'watermark_path': watermark_path,
                'start': start,
                'end': end,
                'chunk_num': i + 1,
                'total_chunks': len(chunks)
            }).encode('utf-8')
            pub_client.publish(topic_name, data)

    #publish_messages()





subscription_id = 'image--watermark-sub1'

def initialize_subscriber():

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    # def callback(message):
    #     # Decode the bytestring to a JSON string
    #     json_str = message.data.decode('utf-8')
    #     # Parse the JSON string to a map object
    #     data = json.loads(json_str)
    #     print(f"Received message: {data}")
    #     message.ack()

    
    def callback(message): #处理来自pub的消息
        data = json.loads(message.data.decode('utf-8'))
        print(f"Received message: {data}")

        process_chunk(data['job_id'], data['video_url'], data['watermark_path'], data['start'], data['end'])
        message.ack()

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}...\n")


thread = threading.Thread(target=initialize_subscriber)