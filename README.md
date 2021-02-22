# HeraSDG-BigDataAnalyticsPipeline
This repositories contains my thesis project for the Master Degree in Computer Engineering.

### 1. Setup the cluster (eg minikube start)

### 2. Install helm

### 3. Deploy HDFS on cluster (using Helm):  
- Firstly, add the [gradiant/hdfs chart](https://artifacthub.io/packages/helm/gradiant/hdfs) to the local Helm repository list:  
`helm repo add gradiant https://gradiant.github.io/charts`  
- Then, deploy the release on the cluster, providing the custom value in the file my-kakfa-values.yaml:  
`helm install -f my-hdfs-values.yaml my-hdfs gradiant/hdfs`  

### 4. Deploy Kafka on cluster (using Helm):  
- Firstly, add the [bitnami/kafka chart](https://artifacthub.io/packages/helm/bitnami/kafka) to the local Helm repository list:  
`helm repo add bitnami https://charts.bitnami.com/bitnami`  
- Then, deploy the release on the cluster, providing the custom value in the file my-kakfa-values.yaml:  
`helm install -f my-hdfs-values.yaml my-kafka bitnami/kafka`  
