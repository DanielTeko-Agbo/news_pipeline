from confluent_kafka import Producer
from configparser import ConfigParser
import requests
from pprint import pprint
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import List
import uuid
from datetime import datetime
from dateutil import parser
import logging
from logging.handlers import RotatingFileHandler
import os
import time

logging.basicConfig(
    format="%(asctime)s - %(funcName)s -  %(levelname)s => %(message)s",
    level=logging.INFO,
    handlers=[
        RotatingFileHandler(
            filename="/src/logs/latest_news_producers.log",
            mode="a",
            maxBytes=10000000,
            backupCount=5,
        )
    ],
)

# Setting up the config object
config = ConfigParser()
config.read("/src/producers/.config.ini")

api = config['api'] # Get the api section of the config file.

# Setting up the kafka producer object.
producer = Producer({
    "bootstrap.servers": "newsKafka:9092"
})

# A pydantic class object for our API response
class NewsObject(BaseModel):
    id: uuid.UUID
    author: str
    description: str
    category: List[str]
    image: HttpUrl | str | None
    language: str
    published: datetime 
    title: str
    url: HttpUrl
    
    # A function to convert to datetime the published datetime provided in the response.
    @field_validator('published', mode='before')
    @classmethod
    def convert_to_datetime(cls, value):
        if not value:
            raise ValueError("'Published' value not found")
        value = parser.parse(value)
        return value

# A function to get news from the news endpoint.
def get_news():
    req = requests.get(
        str(api['latest']), 
        params={
            "apiKey": str(api['key']),
            "language": "en"
        },
        stream=True
    )
    
    news = []
    
    for obj in req.json()["news"]:
        try:
            data = NewsObject(**obj)
            logging.info(f"Successfully parsed NewsObject: ID = {data.id}")
        except Exception as e:
            logging.error(f"Failed to parse NewsObject: {e}")
        else:
            data = data.model_dump_json()
            news.append(data)
            
    return news

# Producer callback function.
def callback(err, event):
    if err:
        logging.error(f'Produce to topic {event.topic()} failed for event: {event.key()}')
    else:
        val = event.value().decode('utf8')
        logging.info(f'{val} sent to partition {event.partition()}.')
        
# Get the latest news.
news = get_news()

# Write latest news to the producer.
for new in news:
    producer.produce('news', str(new).encode('utf8'), on_delivery=callback)
producer.flush()
        
time.sleep(1800)