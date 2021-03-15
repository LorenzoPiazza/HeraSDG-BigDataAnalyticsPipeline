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
from kafka import KafkaProducer
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

def random_id_utenti(size, newId, minBalance=0, p=None):
    """
    Generate size-length ndarray of user_id.
    The user id as the format PartnerId + sequenceNumber, where PartnerId is in [HE, CO, CA], and sequenceNumber is a unique integer.
    For example: HE_123 identifies the 123th user of Hera.
    """
    if not p:
        # default probabilities
        p = (0.5, 0.30, 0.19, 0.01) 
    
    partner_id = ("HE", "CO", "CA", "")
    user_id    = []
    global sequenceNumber  #'global' keyword is necessary otherwise the function define another sequenceNumber variable with a scope local to the function
    
    for el in np.random.choice(partner_id, size = size, p = p):
        if(newId):
            #generate a new user_id
            if(el != ""):
                id = el + "_" + str(sequenceNumber)         
                sequenceNumber = sequenceNumber + 1
                balance[id] = 0
            user_id.append(id)
            existing_user_id.append(id)
        elif(minBalance > 0):
            #retrieve an existing user_id with at least "minBalance" Token available
            allowed_ids = [ key for (key,value) in balance.items() if value >= minBalance ]
            if(len(allowed_ids) >= 1):
                user_id.append(np.random.choice(allowed_ids))
            else:
                user_id.append("") #Any user has the right amount
        else:
            #retrieve a random existing user_id
            user_id.append(np.random.choice(existing_user_id)) 
    return user_id

def random_birthdates(size):
    """Generate random dates within range between start and end."""
    birthdates = []
    for _ in range(size):
        birthdates.append(fake.date_of_birth(minimum_age=18, maximum_age=90))
    return birthdates

def calculateAge(birthDates):
    ages = []
    for d in birthDates:
        today = date.today() 
        age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
        ages.append(age)      
    return ages 

def random_genders(size, p = None):
    """Generate size-length ndarray of genders."""
    if not p:
        # default probabilities
        p = (0.49, 0.50, 0.01)
    gender = ("M", "F", "")
    return np.random.choice(gender, size = size, p = p)

def random_provincie(size, p = None):
    """Generate size-length ndarray of cities."""
    if not p:
        # default probabilities
        p = (0.25, 0.25, 0.25, 0.24, 0.01)
    province = ("BO", "MO", "RE", "PAR", "")
    return np.random.choice(province, size = size, p = p) 


def generate_user_record(size): 
    users_df = pd.DataFrame(columns = ['id_utente', 'Sesso', 'Data di Nascita', 'Eta', 'Provincia'])
    users_df['id_utente']           = random_id_utenti(size=size, newId=True)
    users_df['Sesso']               = random_genders(size) 
    users_df['Data di Nascita']     = random_birthdates(size)
    users_df['Eta']                 = calculateAge(users_df['Data di Nascita'])
    users_df['Provincia']           = random_provincie(size)
    return users_df


   ##################################### "COMPORTAMENTI GENERATOR" #####################################

def random_comportamenti(size):
    comportamenti    = []
    partner_erogante = []
    reward           = []
    id_utenti        = []
    for _ in range(size):
        c = fake.random_element(elements = [('HERA', 'Autolettura consumo gas', 1.6), \
                                           ('HERA', 'Invio elettronico della bolletta', 1.75), \
                                           ('HERA', 'Acquisto energia elettrica da fonti rinnovabili', 2.85), \
                                           ('CONAD', 'Acquisto di prodotti sostenibili', 2.55), \
                                           ('CONAD', 'Recupero bottiglie di plastica', 0.9), \
                                           ('CAMST', 'Acquisto piatti e menu sostenibili', 2.4)] )
        partner_erogante.append(c[0])
        comportamenti.append(c[1])
        reward.append(c[2])
        id = random_id_utenti(size = 1, newId = False)
        balance[id[0]] += c[2]
        id_utenti.append(id[0])
    return comportamenti, partner_erogante, reward, id_utenti

def generate_comportamenti_record(size): 
    comportamenti_df = pd.DataFrame(columns=['comportamento', 'id_utente', 'Partner_erogante', 'reward(tk)'])
    comportamenti_df['comportamento'], comportamenti_df['Partner_erogante'], comportamenti_df['reward(tk)'], comportamenti_df["id_utente"] = random_comportamenti(size)
    return comportamenti_df
   
    
   ##################################### "PREMI GENERATOR" #####################################

def random_premi(size):
    premi            = []
    partner_erogante = []
    prezzi           = []
    id_utenti        = []
    for _ in range(size):
        p = fake.random_element(elements = [('HERA', 'Sconto in bolletta 10€ Hera', 10), \
                                           ('CONAD', 'Buono Spesa 5€ Conad', 5), \
                                           ('CONAD', 'Buono Spesa 5€ Conad', 10),
                                           ('CAMST', 'Buono Spesa 5€ Camst', 5)] )
        partner_erogante.append(p[0])
        premi.append(p[1])
        prezzi.append(p[2])
        id = random_id_utenti(size = 1, newId = False, minBalance = p[2])
        if(id[0] != ''):
            balance[id[0]] -= p[2]  #subtract the price from the balance only if the reward has been registered correctly.
        id_utenti.append(id[0])
    return premi, partner_erogante, prezzi, id_utenti

def generate_premi_record(size):
    premi_df = pd.DataFrame(columns=['premio', 'id_utente', 'Partner_erogante', 'prezzo(tk)'])
    premi_df['premio'], premi_df['Partner_erogante'], premi_df['prezzo(tk)'], premi_df["id_utente"] = random_premi(size)
    return premi_df

# def main(argv):
#    print(len(argv))
#    if len(argv) != 2:
#     print ('Usage: data_source.py -s <kafka_server> -t <topic_name>')
#     #return;

#    try:
#       opts, args = getopt.getopt(argv,"h",["help"])
#    except getopt.GetoptError:
#       print ('Usage: data_source.py -s <kafka_server> -t <topic_name>')
#       sys.exit(2)
#    print(opts)
#    print(args)

#    kafka_server = ''
#    topic_name = ''

def on_send_success(record_metadata):
    print(record_metadata.topic)
    print(record_metadata.partition)
    print(record_metadata.offset)

def on_send_error(excp):
    print('I am an errback' + excp)
    # handle exception

if __name__ == "__main__":
   # Check the arguments passed to the CL (excluding the script name)
   if(len(sys.argv) - 1 != 2): 
        print ('Error: "data_source.py" requires 2 arguments\n')
        print ('Usage: data_source.py <kafka_server> <topic_name>')
        sys.exit(1)
   else:
        kafka_server = sys.argv[1]
        topic_name = sys.argv[2]

   # Create a producer and a connection to the Kafka Broker
   producer = KafkaProducer(bootstrap_servers=[kafka_server], 
                            value_serializer=lambda x: dumps(x).encode('utf-8'))
   print("...Connecting to broker " + kafka_server + " on topic " + topic_name)
   print()
   if(producer.bootstrap_connected()):
        print("Initial connection established")
      #   print(producer.DEFAULT_CONFIG)
        for i in range(3):
            user = generate_user_record(1)
            # print(data.__sizeof__())
            future = producer.send(topic_name, value=user.to_json())
            try:
                record_metadata = future.get(timeout=10)
            except KafkaError as e:
                # Decide what to do if produce request failed...
                print(e)
                pass
            # producer.flush() 
            # sleep(2)
   else:
        print("Something wrong in the initial connection to Kafka Server")
        sys.exit(2)
   # users = generate_user_record(1000)
   # users.to_csv("users.csv")     
   