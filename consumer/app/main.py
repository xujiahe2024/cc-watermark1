import threading
import os
import sys
import logging
import time
import consumer.app.message_queue1 as message_queue1

# Configure the logging module to print to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)






bucketname = 'ccmarkbucket'
#topic_name = 'projects/watermarking-424614/topics/image-watermark-sub'



if __name__ == '__main__':
    threading.Thread(target=message_queue1.initialize_subscriber).start()
    while True:
        time.sleep(1)
