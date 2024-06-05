from google.cloud import pubsub_v1

import json


project_id = "watermarking-424614"
topic_id = "image-watermark-sub"

def initialize_publisher():
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    """
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
    def publish_messages(video_url, start, end):
        if video_url and start and end:
            # Create a map object
            data = {
                "video_url": video_url,
                "start": start,
                "end": end
            }
            # Convert the map object to a JSON string
            data = json.dumps(data)
            # Data must be a bytestring
            data = data.encode("utf-8")
            # Publish a message
            future = publisher.publish(topic_path, data)
            print(f"Published {data} to {topic_path}: {future.result()}")

    #publish_messages()





subscription_id = 'image--watermark-sub1'

def initialize_subscriber():

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    def callback(message):
        # Decode the bytestring to a JSON string
        json_str = message.data.decode('utf-8')
        # Parse the JSON string to a map object
        data = json.loads(json_str)
        print(f"Received message: {data}")
        message.ack()

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}...\n")

    # 让订阅者运行一段时间，然后停止
    try:
        streaming_pull_future.result(timeout=30)
    except TimeoutError:
        streaming_pull_future.cancel()  # Trigger the shutdown.
        streaming_pull_future.result()  # Block until the shutdown is complete.
