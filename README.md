# HeraSDG-BigDataAnalyticsPipeline
This repository contains my thesis project for the Master Degree in Computer Engineering.

### 1. Setup the cluster (eg minikube start)

### 2. Install helm

### 3. Deploy Kafka on cluster (using Helm):  
- Firstly, add the [bitnami/kafka chart](https://artifacthub.io/packages/helm/bitnami/kafka) to the local Helm repository list:  
`helm repo add bitnami https://charts.bitnami.com/bitnami`  
- Then, deploy the release on the cluster, providing the custom values in the file my-kakfa-values.yaml:  
`helm install -f my-kafka-values.yaml my-kafka bitnami/kafka`

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

**Keep in mind that** the first connection to the boostrap server will return to the producer some metadata with the addresses on which the broker (or the brokers) could be reached.  These metadata are called *advertisedListeners* and are configurable on the *server.properties* file on the kafka broker. The advertised listener returned to the client is then used to establish the connection on which send the data.  
In my configuration, the advertised listener returned is `127.0.0.1:30001`.  The host address is configurable in the values *.Values.externalAccess.service.domain* of the *my-kafka-values.yaml*. It will determine how the scripts-configmap will be templated and how the server.properties will be written.  
For more details consult the scripts-configmap.yaml source file of the bitnami/kafka helm chart.

#### Launch a Kafka Debugger Pod with Kafkacat (optional):
1. `kubectl run kafkacat-debugger --image=edenhill/kafkacat:1.6.0 --restart=Never --command -- sleep 999d`  
2. Open a shell in the Pod and use the Kafkacat tool.  
For example, to inspect the metadata returned to the client:  
`kafkacat -b <bootstrap-server:port> -t <topic> -L`

### 4. Deploy HDFS on cluster (using Helm):  
- Firstly, add the [gaffer/hdfs chart](https://artifacthub.io/packages/helm/gaffer/hdfs) to the local Helm repository list:  
`helm install my-hdfs gaffer/hdfs --version 0.10.0`  
- Then, deploy the release on the cluster, providing the custom value in the file my-kakfa-values.yaml:  
`helm install -f my-hdfs-values.yaml my-hdfs gaffer/hdfs --version 0.10.0`
- If you want, you can create a port-forward to access the hdfs manager UI:  
 `kubectl port-forward -n default svc/my-hdfs-namenodes 9870:9870`

   Then open the ui in your browser:

   open http://localhost:9870


### 5. Deploy Spark on cluster (using Helm):  
`helm install my-spark bitnami/spark -f my-spark-values.yaml`

#### Notes:  
1. Get the Spark master WebUI URL by running these commands:

  `kubectl port-forward --namespace default svc/my-spark-master-svc 8080:80`
  open http://localhost:8080


### 6. Deploy the Preprocessor component on cluster:

### 7. Deploy the ML-Frontend component on cluster (using Helm):
`helm repo add gradiant https://gradiant.github.io/charts/`  
`helm install my-jupyter gradiant/jupyter --version 0.1.6 -f ./ML-Frontend/my-jupyter-values.yaml`

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
The command removes all the Kubernetes components associated with the chart and deletes the release. Use the option --purge to delete all persistent volumes too.



