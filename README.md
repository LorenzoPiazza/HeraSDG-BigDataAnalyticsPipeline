# HeraSDG-BigDataAnalyticsPipeline
This repositories contains my thesis project for the Master Degree in Computer Engineering.

### 1. Setup the cluster (eg minikube start)

### 2. Install helm

### 3. Deploy HDFS on cluster (using Helm):  
- Firstly, add the [gaffer/hdfs chart](https://artifacthub.io/packages/helm/gaffer/hdfs) to the local Helm repository list:  
`helm install my-hdfs gaffer/hdfs --version 0.10.0`  
- Then, deploy the release on the cluster, providing the custom value in the file my-kakfa-values.yaml:  
`helm install -f my-hdfs-values.yaml my-hdfs gaffer/hdfs --version 0.10.0`
- If you want, you can create a port-forward to access the hdfs manager UI:  
 `kubectl port-forward -n default svc/my-hdfs-namenodes 9870:9870`

   Then open the ui in your browser:

   open http://localhost:9870


### 4. Deploy Kafka on cluster (using Helm):  
- Firstly, add the [bitnami/kafka chart](https://artifacthub.io/packages/helm/bitnami/kafka) to the local Helm repository list:  
`helm repo add bitnami https://charts.bitnami.com/bitnami`  
- Then, deploy the release on the cluster, providing the custom value in the file my-kakfa-values.yaml:  
`helm install -f my-kafka-values.yaml my-kafka bitnami/kafka`  

### 5. Deploy Spark on cluster (using Helm):  


### Delete/Uninstall a Helm release:
You can see all the release deployed with the command:  
`helm list`  
Then you can choose to uninstall one of them with the command:  
`helm delete <release-name>`  
The command removes all the Kubernetes components associated with the chart and deletes the release. Use the option --purge to delete all persistent volumes too.
