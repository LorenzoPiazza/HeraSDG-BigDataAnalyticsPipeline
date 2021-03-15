from kafka import KafkaConsumer
import sys

if __name__ == "__main__":
   # Check the arguments passed to the CL (excluding the script name)
   if(len(sys.argv) - 1 != 2): 
        print ('Error: "simple_kafka_consumer.py" requires 2 arguments\n')
        print ('Usage: simple_kafka_consumer.py <kafka_server> <topic_name>')
        sys.exit(1)
   else:
        kafka_server = sys.argv[1]
        topic_name = sys.argv[2]

consumer = KafkaConsumer(topic_name, bootstrap_servers = kafka_server)
for msg in consumer:
     print (msg)