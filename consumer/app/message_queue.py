from google.cloud import pubsub_v1
from worker import process_chunk
import json
import threading
import logging
from urllib.parse import unquote




project_id = "watermarking-424614"
topic_id = "image-watermark"


pub_client = pubsub_v1.PublisherClient()
topic_path = pub_client.topic_path(project_id, topic_id)


topic_name = 'projects/{project_id}/topics/{topic}'.format(
    project_id=project_id,
    topic=topic_id, 
)


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

    # def publish_messages(video_url, start, end):
    #     if video_url and start and end:
    #         
    #         data = {
    #             "video_url": video_url,
    #             "start": start,
    #             "end": end
    #         }
    #         # Convert the map object to a JSON string
    #         data = json.dumps(data)
    #         
    #         data = data.encode("utf-8")
    #         # Publish a message
    #         future = publisher.publish(topic_path, data)
    #         print(f"Published {data} to {topic_path}: {future.result()}")

def publish_messages(job_id, video_path, watermark_path, chunks):
        logging.info(f"Topic path: {topic_path}")
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
            future = pub_client.publish(topic_name, data)
            logging.info(f"Published message {i + 1} to {topic_name}")
            logging.info.info(f"Published message future: {future.result()}")

    #publish_messages()





subscription_id = 'image--watermark-sub1'

subscription_name = 'projects/{project_id}/subscriptions/{sub}'.format(
    project_id=project_id,
    sub=subscription_id, 
)

def callback(message): 
            
        try:
            data = json.loads(message.data.decode('utf-8'))
                #logging.info(f"Received message : {data}")
                
                # Decode the URL
                #video_url = unquote(data['video_url'])

            process_chunk(data['job_id'], "", data['start'], data['end'], data['chunk_num'], data['total_chunks'])
            message.ack()
        except Exception as e:
            logging.info(f"An error occurred while processing message: {e}")
            message.ack()


def initialize_subscriber():
    for i in range(3):
        #current_app.logger.info(f"Subscription name: {subscription_name}")
        subscriber = pubsub_v1.SubscriberClient()
        #subscriber2 = pubsub_v1.SubscriberClient()
        #subscriber3 = pubsub_v1.SubscriberClient()
        
        subscription_path = subscriber.subscription_path(project_id, subscription_id)

        #subscriber2.subscribe(subscription_path, callback=callback)
        #subscriber3.subscribe(subscription_path, callback=callback)
        streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    logging.info(f"Listening for messages on {subscription_path}\n")
    logging.info(f"streaming_pull_future: {streaming_pull_future}")


