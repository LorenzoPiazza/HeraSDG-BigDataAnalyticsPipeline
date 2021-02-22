### data_source.py

### This script has the goal to simulate a DataSource of the project.
### It generates some mock data and publishes them to the Ingestor's component (so to the Kafka topic).
### This script run outside the cluster because I think also the real Data Sources will be.
### It is a Python Kafka producer (docs: https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html)


### If you don't have kafka-python already installed, you have to run
### >>> pip install kafka-python

from kafka import KafkaProducer
from json import dumps
from time import sleep
import sys, getopt


def main(argv):
   print(len(argv))
   if len(argv) != 2:
    print ('Usage: data_source.py -s <kafka_server> -t <topic_name>')
    #return;

   try:
      opts, args = getopt.getopt(argv,"h",["help"])
   except getopt.GetoptError:
      print ('Usage: data_source.py -s <kafka_server> -t <topic_name>')
      sys.exit(2)
   print(opts)
   print(args)
   
   kafka_server = ''
   topic_name = ''
   # for opt, arg in opts:
      # if opt == '-h':
         # print ('Usage: \ndata_source.py -s <kafka_server> -t <topic_name>')
         # sys.exit()
      # elif opt in ("-s", "--kafka_server"):
         # kafka_server = arg
      # elif opt in ("-t", "--topic_name"):
         # topic_name = arg
   # print ('kafka_server is', kafka_server)
   # print ('topic name is', topic_name)
      
if __name__ == "__main__":
   #Check the arguments passed to the CL (excluding the script name)
   if(len(sys.argv) - 1 != 2): 
        print ('Error: "data_source.py" requires 2 arguments\n')
        print ('Usage: data_source.py <kafka_server> <topic_name>')
        sys.exit(1)
   else:
        kafka_server = sys.argv[1]
        topic_name = sys.argv[2]
 
   print(kafka_server)
   #Create a producer and a connection to the Kafka Broker
   producer = KafkaProducer(bootstrap_servers=[kafka_server], 
                            value_serializer=lambda x: dumps(x).encode('utf-8'))

   if(producer.bootstrap_connected()):
        for i in range(3):
            data = { 'number' : i }
            producer.send(topic_name, value=data)
            print(data)
            sleep(5)
   else:
        print("Something wrong in the connection to Kafka Server")
        sys.exit(2)