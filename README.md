## NEWS PIPELINE

In this project, news from an [API](https://api.currentsapi.services/v1/latest-news) is consumed and written to a kafka topic. 

Messages sent to the kafka topic are subsequently consumed, processed and the processed data stored in a MongoDB database.

> *NEXT STEPS*
Use an orchestrator instead of bash script to run the various scripts.