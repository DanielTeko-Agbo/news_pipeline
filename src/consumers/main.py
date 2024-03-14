from confluent_kafka import Consumer, KafkaError, KafkaException
import json
from configparser import ConfigParser
from pprint import pprint
from dateutil import parser
import logging
from logging.handlers import RotatingFileHandler
import os
import time
from pymongo import MongoClient, errors

logging.basicConfig(
    format="%(asctime)s - %(levelname)s => %(message)s",
    level=logging.INFO,
    handlers=[
        RotatingFileHandler(
            filename="/src/logs/consumer.log",
            mode="a",
            maxBytes=10000000,
            backupCount=5,
        )
    ],
)

# Setting up the config object
config = ConfigParser()
config.read("/src/consumers/.config.ini")
conn = config['mongo']

#Setting up a mongo connection object.
mongo = MongoClient(f"mongodb://{conn['user']}:{conn['passwd']}@{conn['host']}:{conn['port']}")
db = mongo["newsDB"]
collection = db["news"]    

# Setup consumer object
consumer = Consumer({
    "bootstrap.servers": "newsKafka:9092",
    "group.id": "news_consumer_0009",
    "auto.offset.reset": "earliest"
})

# Function to transform author value.
def get_author(author):
    if "@" in author: return author.split('@')[-1].strip()
    elif "|" in author: return author.split('|')[0].strip()
    elif "[" in author: return None
    elif author == "": return None
    elif "http" in author: return None
    
    else: return author.strip()
    

doc_list = [] # Initialize array to contain records.
start_time = time.time()
  
try:
    consumer.subscribe(["news"])
    
    try:
        while True:
            msg = consumer.poll(1.0)
        
            if not msg:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logging.error('%% %s [%d] reached end at offset %d\n' %(msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    logging.error(KafkaException(msg.error()))
            else:
                
                value = json.loads(msg.value().decode("utf8"))
                
                data = dict(
                    author= get_author(str(value["author"])),
                    category=value["category"],
                    description=value["description"],
                    _id=value["id"],
                    image=value["image"] if str(value["image"]).startswith("http") else None,
                    language="English" if value["language"] == "en" else value["language"],
                    published=parser.parse(value["published"]).strftime("%Y-%m-%dT%H:%M:%S"),
                    title=value["title"],
                    url=value["url"]
                )
                
                try:
                    collection.insert_one(data)
                    logging.info(f"Successfully passed data to MongoDB: {data['_id']}")
                except Exception as e:
                    logging.error(f"Unable to pass data to MongoDB: {e}")
                
                # # Insert processed message to the doc_list array.
                # doc_list.append(data)
                
                # # Confirm list size and elapsed time to pass data to mongo
                # if len(doc_list) >= 1000 or (time.time() - start_time) >= 120:
                #     try:
                #         collection.insert_many(doc_list)
                #         logging.info(f"Successfully passed data to MongoDB: {len(doc_list)} records")
                #         doc_list.clear()
                #         start_time = time.time()
                #     # except errors.DuplicateKeyError as e:
                #     #     logging.error(f"Duplicate id encountered: {e}")
                #     except Exception as e:
                #         logging.error(f"Unable to pass data to MongoDB: {e}")
                #         continue     
                                    
    except Exception as err:
        logging.error(f"Error reading messages: {err}")
except Exception as err:
    logging.error(f"An error occured: {err}")