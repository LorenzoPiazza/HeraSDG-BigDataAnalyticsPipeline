# HeraSDG-BigDataAnalyticsPipeline
> This repository contains my thesis project for the Master Degree in Computer Engineering.  
> Here it is the documentation to reproduce the project. Have fun!

- [HeraSDG-BigDataAnalyticsPipeline](#herasdg-bigdataanalyticspipeline)
    - [1. Setup the Kubernetes cluster](#1-setup-the-kubernetes-cluster)
    - [2. Install Helm](#2-install-helm)
    - [3. Deploy HDFS on cluster (using Helm):](#3-deploy-hdfs-on-cluster-using-helm)
    - [4. Deploy Kafka on cluster (using Helm):](#4-deploy-kafka-on-cluster-using-helm)
      - [4.1 Kafka Connect: Confluent HDFS3 Sink Connector](#41-kafka-connect-confluent-hdfs3-sink-connector)
    - [5. Deploy the ML-Frontend equipped with Spark component on cluster (using Helm):](#5-deploy-the-ml-frontend-equipped-with-spark-component-on-cluster-using-helm)
      - [How to access the frontend:](#how-to-access-the-frontend)
    - [Delete/Uninstall a Helm release:](#deleteuninstall-a-helm-release)

### 1. Setup the Kubernetes cluster
Firstly you have to create a K8s cluster on which deploy the Big Data Analytics pipeline.  
You can either choose to set up a local environment with a single virtual node cluster, or set up a real cluster.  
- For the first option you can follow this guide: **[How to set up a minikube local cluster](https://minikube.sigs.k8s.io/docs/start/)**.  
    > *And then [install kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl) to talk to the cluster.*  

- Otherwise look at this guide: **[How set up a Kubernetes cluster](https://github.com/LorenzoPiazza/HeraSDG-BigDataAnalyticsPipeline/blob/master/SETUP_K8s_CLUSTER.md)**.  
    > *You will end up with a K8s on premise cluster and your laptop acting as an external workstation.*

### 2. Install Helm
Now you have to install Helm, a package manager for K8s. It helps to deploy software on K8s.  
> You can follow this [installation guide](https://helm.sh/docs/intro/install/).  

Then, you have to configure kubectl to talk to the right cluster. Helm, infact, will refer to the current kubectl context.  
**Note:** If you installed minikube and you have only that cluster, kubectl is already configured.  
Otherwise, if you have more than one K8s cluster, you should configure kubectl to talk to the right cluster.
> If you haven't already, follow step 4, 5, 6, 7 of [Configure your laptop to act as an external cluster workstation](https://github.com/LorenzoPiazza/HeraSDG-BigDataAnalyticsPipeline/blob/master/SETUP_K8s_CLUSTER.md#optional-configure-your-laptop-to-act-as-an-external-cluster-workstation)

<br> 

The initial setup ends here. You can **start to deploy the pipeline components!**    

### 3. Deploy HDFS on cluster (using Helm):
The helm chart that I used deploys an HDFS 3.2.1 cluster with a namenode and 3 datanodes.  
The replica factor I set is 3, and the block-size is 128Mb.
- Firstly, add the **gaffer/** Helm repository to your local repository list:  
`helm install my-hdfs gaffer/hdfs --version 0.10.0`  
- Then, deploy a [gaffer/hdfs](https://artifacthub.io/packages/helm/gaffer/hdfs) release on the cluster, providing the custom value in the file my-kakfa-values.yaml:  
`helm install -f my-hdfs-values.yaml my-hdfs gaffer/hdfs --version 0.10.0`
- If you want, you can create a port-forward to access the hdfs manager UI:  
 `kubectl port-forward -n default svc/my-hdfs-namenodes 9870:9870`

   Then open the ui in your browser:

   open `http://localhost:9870`

**Debugging:**
You can use the hdfs-shell Pod to execute some useful commands on the HDFS deployed.  

POSSIBLE ERRORS:  
After an unexpected stop of the HDFS connector (e.g. after a computer freeze) it can happen that the connector doesn't restart correctly and print this ERROR on the log:  
```
ERROR Recovery failed at state RECOVERY_PARTITION_PAUSED (io.confluent.connect.hdfs3.TopicPartitionWriter:273)
org.apache.kafka.connect.errors.DataException: Error creating writer for log file hdfs://my-hdfs-namenodes:8020//tmp/utenti/0/log
.
.
.
Caused by: org.apache.hadoop.hdfs.CannotObtainBlockLengthException: Cannot obtain block length for LocatedBlock ... of <file>.
```
 
It happens because there is a file still in written state, not closed correctly because the previous connectors has stopped.
 
You can solve as follows:  
You can use fsck (Filesystem check to run a DFS filesystem checking utility) on a particular directory to check if there are some openwrite file:  
  `hdfs fsck /`
  or
  `hdfs fsck / -openforwrite`    
If so, require the namenode to [recover the lease](https://blog.cloudera.com/understanding-hdfs-recovery-processes-part-1/) for that file:    
  `hdfs debug recoverLease -path /tmp/premi/0/log`

### 4. Deploy Kafka on cluster (using Helm):  
- Firstly, add the **bitnami/** Helm repository to your local repository list:  
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

### 5. Deploy the ML-Frontend equipped with Spark component on cluster (using Helm):
In this section we deploy a **Jupyter release that is equipped with PySpark 3.1.1**. This release uses the [*jupyter/pyspark-notebook*](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-pyspark-notebook) image and will create a Stateful Set, of one Pod, that contains the frontend notebook.  
This notebook is configured to [run Spark on Kubernetes](https://spark.apache.org/docs/latest/running-on-kubernetes.html) in *client mode*. It means that, when the user require the Spark Context creation, the desired # of executor are created (in Pods) and the Spark Driver is launched in the same Pod of the notebook.   
The executor use the [*lorenzopiazza/hera_sdg:spark-py_3.1.1-python3.8*](https://hub.docker.com/layers/lorenzopiazza/hera_sdg/spark-py_3.1.1-python3.8/images/sha256-8f2643f9c565a64c8ffbe38b798d5ce1b8b9be2fa414a8a0081f5d39974bb481?context=repo) image, a custom image that I create from the Pyspark 3.1.1 image and make available on my docker hub.


- Firstly, add the **gradiant/** Helm repository to your local repository list:  
`helm repo add gradiant https://gradiant.github.io/charts/`  
- Then, deploy a [gradiant/jupyter](https://artifacthub.io/packages/helm/gradiant/jupyter) release on the cluster, providing the custom values in the file /ML-Frontend/my-jupyter-values.yaml:  
`helm install my-jupyter gradiant/jupyter --version 0.1.6 -f ./ML-Frontend/my-jupyter-values.yaml`

Using the *gitNotebooks* value, you can custom the release with an init Container that download an *entire* Github repo (with your custom notebooks) and make them available inside the Pod.  

- For driver-executor communication purpose you have also to create an *headless service* that refers the Frontend Pod where the Spark Driver execute:  
`kubectl apply -f ./ML-Frontend/jupyter-headless-svc.yaml`

#### How to access the frontend:
1. Get access token from jupyter server log:  
   `kubectl logs -f -n default svc/my-jupyter-jupyter`

2. Create a port-forward to the jupyter:  
   `kubectl port-forward -n default svc/my-jupyter-jupyter 8888:8888`

3. Then open the ui in your browser and use the access token:  
   open `http://localhost:88888`

If you set up your own password, remember to restart jupyter server to update the configuration.
  File -> Shut Down


### Delete/Uninstall a Helm release:
You can see all the release deployed with the command:  
`helm list`  
Then you can choose to uninstall one of them with the command:  
`helm delete <release-name>`  
The command removes all the Kubernetes components associated with the chart and deletes the release, but doesn't delete the PVs and PVCs.


<br> 

***
Author: [Lorenzo Piazza](https://github.com/LorenzoPiazza)
