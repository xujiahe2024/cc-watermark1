import threading
import os
import sys
import logging
import time
from google.cloud import storage, firestore, pubsub_v1
try:
    from consumer.app.worker2 import split_video, merge_chunks, process_chunk
    import consumer.app.message_queue1 as message_queue1
    import uuid
    import json
except Exception as e:
    print(f"An error occurred while importing modules: {e}")

# Configure the logging module to print to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

output_dir = os.path.abspath('./output')

storage = storage.Client()
database = firestore.Client()





bucketname = 'ccmarkbucket'
publisher = pubsub_v1.PublisherClient()
#topic_name = 'projects/watermarking-424614/topics/image-watermark-sub'



if __name__ == '__main__':
    threading.Thread(target=message_queue1.initialize_subscriber).start()
    while True:
        time.sleep(1)
