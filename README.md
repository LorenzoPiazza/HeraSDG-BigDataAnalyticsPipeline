# HeraSDG-BigDataAnalyticsPipeline
This repository contains my thesis project for the Master Degree in Computer Engineering.

### 1. Setup the cluster (eg minikube start)

### 2. Install helm

### 3. Deploy HDFS on cluster (using Helm):
The helm chart that I used deploys an HDFS 3.2.1 cluster with a namenode and 3 datanodes.  
The replica factor I set is 3, and the block-size is 128Mb.
- Firstly, add the **gaffer/** Helm charts to the local Helm repository list:  
`helm install my-hdfs gaffer/hdfs --version 0.10.0`  
- Then, deploy a [gaffer/hdfs](https://artifacthub.io/packages/helm/gaffer/hdfs) release on the cluster, providing the custom value in the file my-kakfa-values.yaml:  
`helm install -f my-hdfs-values.yaml my-hdfs gaffer/hdfs --version 0.10.0`
- If you want, you can create a port-forward to access the hdfs manager UI:  
 `kubectl port-forward -n default svc/my-hdfs-namenodes 9870:9870`

   Then open the ui in your browser:

   open http://localhost:9870

**Debugging:**
You can use the hdfs-shell Pod to execute some useful commands on the HDFS deployed.  

POSSIBLE ERRORS:  
After an unexpected stop of the HDFS connector (e.g. after a computer freeze) it can happen that the connector doesn't restart correctly and print this ERROR on the log:  
`ERROR Recovery failed at state RECOVERY_PARTITION_PAUSED (io.confluent.connect.hdfs3.TopicPartitionWriter:273)
org.apache.kafka.connect.errors.DataException: Error creating writer for log file hdfs://my-hdfs-namenodes:8020//tmp/utenti/0/log
.
.
.
Caused by: org.apache.hadoop.hdfs.CannotObtainBlockLengthException: Cannot obtain block length for LocatedBlock ... of <file>.`
 
It happens because there is a file still in written state, not closed correctly because the previous connectors has stopped.
 
You can solve as follows:  
You can use fsck (Filesystem check to run a DFS filesystem checking utility) on a particular directory to check if there are some openwrite file:  
  `hdfs fsck /`
  or
  `hdfs fsck / -openforwrite`    
If so, require the namenode to [recover the lease](https://blog.cloudera.com/understanding-hdfs-recovery-processes-part-1/) for that file:    
  `hdfs debug recoverLease -path /tmp/premi/0/log`

### 4. Deploy Kafka on cluster (using Helm):  
- Firstly, add the **bitnami/** Helm charts to the local Helm repository list:  
`helm repo add bitnami https://charts.bitnami.com/bitnami`  
- Then, deploy a [bitnami/kafka](https://artifacthub.io/packages/helm/bitnami/kafka) release on the cluster, providing the custom values in the file /Kafka/my-kakfa-values.yaml:  
`helm install -f /Kafka/my-kafka-values.yaml my-kafka bitnami/kafka`

    #### Setup the connection between the data_source (external to the cluster) and Kafka (internal to the cluster):
    Kafka is reachable using a K8s NodePort Service that expose the port 30001 on all the node of the cluster.  
This port is configured to proxy the incoming connections to the *my-kafka-0-external* service on its 9094 port. Finally, the service will forward the connection to the *my-kafka-0* pod, which is the Kafka broker.  
However the minikube node has a internal IP which is not reachable from the laptop where the data_source.py is executed.  To resolve this issue a possible solution is:  
    1. Open a console and run the following commands:  
`minikube service my-kafka-0-external --url`  
    2. Open a second console and run:  
`kubectl port-forward svc/my-kafka-0-external 30001:9094`  
    3. Now open a third console and execute the data_source.py:  
`python data_source.py <bootstrap-server:port> <topic>`  
where bootstrap-server is the url returned from `minikube service` command and topic the topic on which we want to publish data.  

    **Keep in mind that** the first connection to the bootstrap server will return to the producer some metadata with the addresses on which the broker (or the brokers) could be reached.  These metadata are called *advertisedListeners* and are configurable on the *server.properties* file on the kafka broker. The advertised listener returned to the client is then used to establish the connection on which send the data.  
In my configuration, the advertised listener returned is `127.0.0.1:30001`.  The host address is configurable in the values *.Values.externalAccess.service.domain* of the *my-kafka-values.yaml*. It will determine how the scripts-configmap will be templated and how the *server.properties* will be written.  
For more details consult the scripts-configmap.yaml source file of the bitnami/kafka helm chart.

    #### Launch a Kafka Debugger Pod with Kafkacat (optional):
    1. Launch then Pod:  
    `kubectl run kafkacat-debugger --image=edenhill/kafkacat:1.6.0 --restart=Never --command -- sleep 999d`  
    2. Open a shell in the Pod and use the Kafkacat tool.  
For example, to inspect the metadata returned to the client:  
`kafkacat -b <bootstrap-server:port> -t <topic> -L`

#### 4.1 Kafka Connect: [Confluent HDFS3 Sink Connector](https://www.confluent.io/hub/confluentinc/kafka-connect-hdfs3)  
*...NOTA: sembra che vi sia una licenza d'uso di 30d. HDFS2 Sink Connector invece dovrebbe essere free...*  

In *my-kafka-values.yaml* file, there is an array field called *extraDeploys*. It defines some extra K8s resources that are deployed with Kafka release when you execute the command `helm install` of the previuos section.  
In particular it deploys:  
- The connector as a Deployment.
- A service to expose it.
- A config map called *my-kafka-connect-config* with the configuration file.
- A config map called *my-kafka-connect-script* with the code to launch the worker and create the HDFS connector.

The connector expose some [REST APIs](https://docs.confluent.io/home/connect/monitoring.html#using-the-rest-interface) for many purpose (debugging, create/pause/restart connectors or tasks, list the configs, etc.).
Some example that you can execute inside the Connector container are:  
- Get the status of *hdfs3-sink* connector and its tasks:  
`curl localhost:8083/connectors/hdfs3-sink/status | python -m json.tool`
- Restart the task with id 0 of the hdfs3-sink connector (there is no output if the command is successful):  
`curl -X POST localhost:8083/connectors/hdfs3-sink/tasks/0/restart`

### 5. Deploy Spark on cluster (using Helm):  
`helm install my-spark bitnami/spark -f my-spark-values.yaml`

#### Notes:  
1. Get the Spark master WebUI URL by running these commands:

  `kubectl port-forward --namespace default svc/my-spark-master-svc 8080:80`
  open http://localhost:8080


### 6. Deploy the ML-Frontend component on cluster (using Helm):
- Firstly, add the **gradiant/** Helm chart to the local Helm repository list:  
`helm repo add gradiant https://gradiant.github.io/charts/`  
- Then, deploy a [gradiant/jupyter](https://artifacthub.io/packages/helm/gradiant/jupyter) release on the cluster, providing the custom values in the file /ML-Frontend/my-jupyter-values.yaml:  
`helm install my-jupyter gradiant/jupyter --version 0.1.6 -f ./ML-Frontend/my-jupyter-values.yaml`

Using the *gitNotebooks* value, you can custom the release with an init Container that download an *entire* Github repo (with your custom notebooks) and make them available inside the Pod.  


#### Notes:
1. Get access token from jupyter server log:
   kubectl logs -f -n default svc/my-jupyter-jupyter

1. Create a port-forward to the jupyter:
   kubectl port-forward -n default svc/my-jupyter-jupyter 8888:8888

Then open the ui in your browser and use the access token:
   open http://localhost:88888

If you set up your own password, remember to restart jupyter server to update the configuration.
  File -> Shut Down


### Delete/Uninstall a Helm release:
You can see all the release deployed with the command:  
`helm list`  
Then you can choose to uninstall one of them with the command:  
`helm delete <release-name>`  
The command removes all the Kubernetes components associated with the chart and deletes the release, but don't delete the PVs and PVCs.



