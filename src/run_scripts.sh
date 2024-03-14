#!/bin/bash

cd /src/producers

nohup python3 gh_news.py &

nohup python3 historic_news.py &

nohup python3 latest_news.py &

cd /src/consumers

nohup python3 main.py &

jobs -l