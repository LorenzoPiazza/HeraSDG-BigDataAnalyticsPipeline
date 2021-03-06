### data_source.py

### This script has the goal to simulate a DataSource of the project.
### It generates some mock data and publishes them to the Ingestor's component (so to the Kafka topic).
### This script run outside the cluster because I think also the real Data Sources will be.
### It is a Python Kafka producer (docs: https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html)


### To install the dependencies you have to run:
### pip install kafka-python
### pip install faker


import sys, getopt
import pandas as pd
import numpy  as np
from kafka import KafkaProducer, BrokerConnection, KafkaAdminClient
from kafka.partitioner import DefaultPartitioner
from kafka.errors import KafkaError
from json  import dumps
from time  import sleep
from faker import Faker
from faker.providers import date_time
from datetime import date 

    
Faker.seed(0) # for reproducibility sake: WARNING: Calling the same methods with the same version of faker and seed produces the same results!
np.random.seed(0)
fake=Faker()
fake.add_provider(date_time) 

sequenceNumber   = 1
existing_user_id = []
balance          = {}


##################################### "USER GENERATOR" #####################################

def random_id_utente(newId, minBalance=0, p=None):
    """
    Generate a user_id.
    The user id as the format PartnerId + sequenceNumber, where PartnerId is in [HE, CO, CA], and sequenceNumber is a unique integer.
    For example: HE_123 identifies the 123th user of Hera.
    """
    if not p:
        # default probabilities
        p = (0.4, 0.30, 0.19, 0.11) 
    
    partner_id = ("HE", "CO", "CA", "")
    global sequenceNumber  #'global' keyword is necessary otherwise the function define another sequenceNumber variable with a scope local to the function
    
    el = np.random.choice(partner_id, p = p)
    if(newId):
        #generate a new user_id
        if(el != ""):
            id = el + "_" + str(sequenceNumber)         
            sequenceNumber = sequenceNumber + 1
            balance[id] = 0
            existing_user_id.append(id)
        else:
            id = el
    elif(minBalance > 0):
        #retrieve an existing user_id with at least "minBalance" Token available
        allowed_ids = [ key for (key,value) in balance.items() if value >= minBalance ]
        if(len(allowed_ids) >= 1):
            id = np.random.choice(allowed_ids)
        else:
            id = "" #Any user has the right amount
    else:
        #retrieve a random existing user_id
        id = np.random.choice(existing_user_id)
    return id

def random_birthdate():
    """Generate random date within range between start and end."""
    return fake.date_of_birth(minimum_age=18, maximum_age=90)

def calculateAge(birthDate):
    today = date.today() 
    age = today.year - birthDate.year - ((today.month, today.day) < (birthDate.month, birthDate.day))
    return age

def random_gender(p = None):
    """Generate a random gender."""
    if not p:
        # default probabilities
        p = (0.4, 0.6)
    gender = ("M", "F")
    return np.random.choice(gender, p = p)

def random_provincia(p = None):
    """Generate size-length ndarray of cities."""
    if not p:
        # default probabilities
        p = (0.5, 0.1, 0.3, 0.1)
    province = ("BO", "MO", "RE", "PAR")
    return np.random.choice(province, p = p) 


def generate_user_record(): 
    user = {}
    birthdate = random_birthdate()
    user["id_utente"]           = random_id_utente(newId=True)
    user["Sesso"]               = random_gender()
    user["Data di Nascita"]     = str(birthdate)
    user["Eta"]                 = calculateAge(birthdate)
    user["Provincia"]           = random_provincia()
    return user



   ##################################### "COMPORTAMENTI GENERATOR" #####################################

def generate_comportamento_record(): 
    c = fake.random_element(elements = [('HERA', 'Autolettura consumo gas', 1.6), \
                                        ('HERA', 'Invio elettronico della bolletta', 1.75), \
                                        ('HERA', 'Acquisto energia elettrica da fonti rinnovabili', 2.85), \
                                        ('CONAD', 'Acquisto di prodotti sostenibili', 2.55), \
                                        ('CONAD', 'Recupero bottiglie di plastica', 0.9), \
                                        ('CAMST', 'Acquisto piatti e menu sostenibili', 2.4)] )
    id_utente = random_id_utente(newId = False)
    balance[id_utente] += c[2]  #add the reward to the balance of the user.
    comportamento = {}
    comportamento["id_utente"]        = id_utente
    comportamento["Partner_erogante"] = c[0]
    comportamento["comportamento"]    = c[1]
    comportamento["reward(tk)"]       = c[2]
    return comportamento
    
   ##################################### "PREMI GENERATOR" #####################################

def generate_premio_record():
    p = fake.random_element(elements = [('HERA', 'Sconto in bolletta 10€ Hera', 10), \
                                        ('CONAD', 'Buono Spesa 5€ Conad', 5), \
                                        ('CONAD', 'Buono Spesa 5€ Conad', 10), \
                                        ('CAMST', 'Buono Spesa 5€ Camst', 5)] )
    id_utente = random_id_utente(newId = False, minBalance = p[2])
    if(id_utente != ""):
        balance[id_utente] -= p[2]  #subtract the price from the balance only if the reward has been registered correctly.
    premio = {}
    premio["id_utente"]        = id_utente
    premio["Partner_erogante"] = p[0]
    premio["premio"]           = p[1]
    premio["prezzo(tk)"]       = p[2]
    return premio


# Mapping dictionary used in main
to_generate = {
    "comportamenti" : generate_comportamento_record,
    "premi" : generate_premio_record,
    "utenti" : generate_user_record
    }


##################################### METADATA FUCTION #####################################
import threading
import pandas as pd

def printMetadata(producer):
  threading.Timer(30.0, printMetadata, (producer,)).start()
  print("METRICS:")
  metrics = producer.metrics()['producer-metrics']
  d = pd.DataFrame(metrics, index = [0])
  d.to_csv("./producer_metrics.csv", mode='a', header=False)
  print(metrics)
#   for key in metrics:
#     # if(key == "request-latency-avg"):
#         print(str(key) + ": " + str(metrics[key]) )


##################################### MAIN FUNCTION #####################################
if __name__ == "__main__":
   # Check the arguments passed to the CL (excluding the script name)
   if(len(sys.argv) - 1 != 2): 
        print ('Error: "data_source.py" requires 2 argument\n')
        print ('Usage: data_source.py <kafka_bootstrap_server> <initial_data_size>')
        sys.exit(1)
   else:
        kafka_server = sys.argv[1]
        initial_size = int(sys.argv[2])
   
   # Create a producer and a connection to the Kafka Broker
   partitioner = DefaultPartitioner()
   producer = KafkaProducer(bootstrap_servers=[kafka_server],
                            # linger_ms = 500,
                            # batch_size = 0,
                            retries = 3,
                            key_serializer=str.encode, 
                            value_serializer=lambda x: dumps(x).encode('utf-8'),
                            # partitioner=partitioner,
                            metrics_num_samples=2,
                            metrics_sample_window_ms=30000)
   print()
   print("...Connecting to bootstrap_server on " + kafka_server)
   print()
   
   if(producer.bootstrap_connected()):
        print("Initial connection established")
        print("==============================")
        print()
        # ## SOME METADATA INSPECTION

        # START PRINTING METADATA  
        # printMetadata(producer)
        # print("SENDING "+str(initial_size)+ " record WITHOUT PARALLELISM")
        # for i in range(initial_size):
        #     user = generate_user_record()
        #     if(user["id_utente"] == ""):
        #         producer.send("test", key=b"NULL RECORD")  # Simulate a NULL value send
        #         print("NULL")
        #     else:
        #         future = producer.send("test", key=str(np.random.randint(10)), value=user)
        #         try:
        #             returned = future.get(timeout=10)
        #         except KafkaError:
        #             # Decide what to do if produce request failed...
        #             pass
        #         print (returned.topic)
        #         print (returned.partition)
        # print("METRICS:")
        # metrics = producer.metrics()['producer-metrics']
        # for key in metrics:
        #     # if(key == "request-latency-avg"):
        #         print(str(key) + ": " + str(metrics[key]) ) 

        ##### WARNING!!! All the record with the same key will be sent to the same topic partition!
        ##### So even if you have multiple partions but only a single key, all the messages will end up in the same partition and processed by the same consumer, NOT EXPLOITING PARALLELISM !!

        # SEND OPERATIONS
        print("Generate and send a first set of " + str(initial_size) + " users and " + str(10*initial_size) + " behaviours...")
        for i in range(initial_size):
            user = generate_user_record()
            if(user["id_utente"] == ""):
                producer.send("utenti", key="NULL RECORD")  # Simulate a NULL value send
            else:
                producer.send("utenti", key=str(user["id_utente"]), value=user)

        for i in range(5*initial_size):
            comportamento = generate_comportamento_record()
            producer.send("comportamenti", key=str(comportamento["id_utente"]), value=comportamento)

        print()
        print("Generate others data...")
        p = (0.60, 0.25, 0.15)
        options = ("comportamenti", "premi", "utenti")
        while(True):
        # for i in range(10):
            choice = np.random.choice(options, p = p)
            # Invoke the correct generator function according to the choice
            data = to_generate[choice]()
            if(data['id_utente'] == ""):
                producer.send(choice, key="NULL RECORD")      # Simulate a NULL value send
            else:
                producer.send(choice, key=str(data["id_utente"]), value=data)


            # print()
            # print("NEW RECORD for: "+ choice)
            # print("================================================================================================================================")
            # print(data)
            # print("================================================================================================================================")
            # sleep(2)
   else:
        print("Something wrong in the initial connection to Kafka Server")
        sys.exit(2)

