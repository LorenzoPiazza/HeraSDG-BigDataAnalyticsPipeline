## HOW TO: Set up a K8s on-premise cluster with Kubeadm

*Following this guide, inspired by the official [Creating a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/) guide, you end up with an on premise K8s Cluster.  
At the end of the guide, you could also find the instructions to set up your laptop as an external cluster workstation*

- [HOW TO: Set up a K8s on-premise cluster with Kubeadm](#how-to-set-up-a-k8s-on-premise-cluster-with-kubeadm)
  - [Before you begin](#before-you-begin)
  - [*Operations to execute on all nodes*](#operations-to-execute-on-all-nodes)
    - [1. Disable swap memory on your node](#1-disable-swap-memory-on-your-node)
    - [2. Letting iptables see bridged traffic](#2-letting-iptables-see-bridged-traffic)
    - [3. Check required ports are open](#3-check-required-ports-are-open)
    - [4. Install Docker](#4-install-docker)
    - [5. Configure Docker](#5-configure-docker)
    - [6. Install KUBEADM KUBELET and KUBECTL](#6-install-kubeadm-kubelet-and-kubectl)
  - [*Operations to execute only on master node*](#operations-to-execute-only-on-master-node)
    - [1. Start the Control Plane](#1-start-the-control-plane)
    - [2. Configure kubectl to use the right kubeconfig file](#2-configure-kubectl-to-use-the-right-kubeconfig-file)
    - [3. Deploy a Pod Network (I choose Flannel)](#3-deploy-a-pod-network-i-choose-flannel)
    - [4. Enable the scheduling of Pods also on Master Node](#4-enable-the-scheduling-of-pods-also-on-master-node)
  - [*Operations to execute only on WORKER node*](#operations-to-execute-only-on-worker-node)
    - [1. Join the cluster](#1-join-the-cluster)
  - [(OPTIONAL) Configure your laptop to act as an external cluster workstation](#optional-configure-your-laptop-to-act-as-an-external-cluster-workstation)
  - [Install the Kubernetes Dashboard](#install-the-kubernetes-dashboard)
  - [Prepare the Persistent Volumes](#prepare-the-persistent-volumes)
  
- - - -
### Before you begin
Check the [node prerequisites](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/#before-you-begin).

- - - -
### *Operations to execute on all nodes*

#### 1. Disable swap memory on your node  
Kubernetes requires that you disable swap memory on any cluster nodes to prevent the kube-scheduler from assigning a Pod to a node that has run out of CPU/memory or reached its designated CPU/memory limit.  
   ```
    sudo swapoff -a
   ```  
Verify it has been disabled: it should return 0  
   ```
    cat /proc/meminfo | grep 'SwapTotal'
   ```  
Disable permanently, also after reboot  
   ```
    sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
   ```  

#### 2. Letting iptables see bridged traffic    
   ```
    cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
    br_netfilter  
    EOF
   ```

   ```
    cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf  
    net.bridge.bridge-nf-call-ip6tables = 1  
    net.bridge.bridge-nf-call-iptables = 1  
    EOF
   ```
   ```
    sudo sysctl --system
   ```

#### 3. Check [required ports](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/#check-required-ports) are open  
If they aren't, OPEN with iptables  
	
Open a single port  
   ```
    sudo iptables -I INPUT -p tcp --dport 6443 -j ACCEPT
   ```
Open multiple contiguos port  
   ```
    sudo iptables -A INPUT -p tcp --match multiport --dports 10250:10252 -j ACCEPT
   ```
Make the current iptables rule persistent, also after reboot. [Here](https://linuxconfig.org/how-to-make-iptables-rules-persistent-after-reboot-on-linux) for more details:  
   ```
    sudo apt-get install iptables-persistent
   ```

#### 4. Install Docker
   ```
    sudo apt-get remove docker docker-engine docker.io containerd runc
   ```
   ```
    sudo apt-get update
   ```
   ```
    sudo apt-get install \  
      apt-transport-https \  
      ca-certificates \  
      curl \  
      gnupg \  
      lsb-release
   ```
	
   ```
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   ```
   ```
    echo \  
      "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \  
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   ```
   ```
    sudo apt-get update
   ```
   ```
    sudo apt-get install docker-ce docker-ce-cli containerd.io
   ```
   Verify docker installation is succeed  
   ```
    sudo docker run hello-world
   ```

#### 5. Configure Docker
   ```
    sudo mkdir /etc/docker
   ```
   ```
    cat <<EOF | sudo tee /etc/docker/daemon.json
    {
      "exec-opts": ["native.cgroupdriver=systemd"],
      "log-driver": "json-file",
      "log-opts": {
        "max-size": "100m"
      },
      "storage-driver": "overlay2"
    }
    EOF
   ```
   ```
    sudo systemctl enable docker
   ```
   ```
    sudo systemctl daemon-reload
   ```
   ```
    sudo systemctl restart docker
   ```


#### 6. Install KUBEADM KUBELET and KUBECTL
   ```
    sudo apt-get update
   ```
   ```
    sudo apt-get install -y apt-transport-https ca-certificates curl
   ```
   ```
    sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
   ```
   ```
    echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
   ```
   ```
    sudo apt-get update
   ```
   ```
    sudo apt-get install -y kubelet kubeadm kubectl
   ```
   ```
    sudo apt-mark hold kubelet kubeadm kubectl
   ```

- - - -
### *Operations to execute only on master node*


#### 1. Start the Control Plane
   ```
    sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-cert-extra-sans=137.204.57.224
   ```
   **Note**:  
    - replace *--pod-network-cidr* with the CIDR required by the Pod Network chosen. (In this case I use Flannel).  
    - replace *--apiserver-cert-extra-sans* with the public ip of your master node.  
    
    
   If everything ok, the *kubeadm init* command should outputs something like:   
   ```
    Your Kubernetes control-plane has initialized successfully!

    To start using your cluster, you need to run the following as a regular user:

      mkdir -p $HOME/.kube
      sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
      sudo chown $(id -u):$(id -g) $HOME/.kube/config

    Alternatively, if you are the root user, you can run:

      export KUBECONFIG=/etc/kubernetes/admin.conf

    You should now deploy a pod network to the cluster.
    Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
      https://kubernetes.io/docs/concepts/cluster-administration/addons/

    Then you can join any number of worker nodes by running the following on each as root:

    kubeadm join 192.168.40.122:6443 --token <token> \
            --discovery-token-ca-cert-hash sha256:<hash>
   ```

#### 2. Configure kubectl to use the right kubeconfig file  
Follow the instructions on output to configure kubectl using the right kubeconfig file.  
The kubeconfig file is necessary to tell *kubectl* how to connect to the API-Server.

#### 3. Deploy a Pod Network (I choose Flannel)
   ```
    kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
   ```
   Watch the Pod status
   ```
    watch kubectl get pods --all-namespaces
   ```
   After some minutes every Pods should be in Running status. And with command
   ```
    kubectl cluster-info
   ```
   you should see that both API Server and CoreDNS are running.  

#### 4. Enable the scheduling of Pods also on Master Node
   ```
    kubectl taint nodes --all node-role.kubernetes.io/master-
   ```

- - - -
### *Operations to execute only on WORKER node*

#### 1. Join the cluster
   ```
    kubeadm join <master-node-host>:<api-server-port> --token <token> \
        --discovery-token-ca-cert-hash sha256:<hash>
   ```  
   NOTE: You can run `kubeadm token create --print-join-command` in Kubernetes master to get the join command that should be executed in Kubernetes nodes.

- - - -
### (OPTIONAL) Configure your laptop to act as an external cluster workstation

1. **Install kubectl** following this [guide](https://kubernetes.io/docs/tasks/tools/#kubectl).
2. **Copy the kubeconfig file** from master node to your laptop. Run this command from your laptop:
```
 scp -i <private_key> <user>@<master_ip>:/home/ubuntu/.kube/config .
```
3. **Modify the kubeconfig file** on your laptop replacing the internal IP of the API Server with its public IP.  
When we run `kubeadmin init` we have infact added that ip to the certified IP list, using the *apiserver-cert-extra-sans* parameter. So, now you can use it.  
4. If you have more than one K8s cluster you should **tell kubectl which cluster you want to interact**.
Since each cluster has its own kubeconfig file, you can create a *KUBECONFIG* environment variable where store the path to all the kubeconfig that you have.  
NOTE 1: by default the kubeconfig file is stored in $HOME/.kube directory and if you don't set KUBECONFIG env kubectl will read that path.   
NOTE 2: each OS want its own specific sep between the paths. Please refer to your OS specific env semantic.  
```
 export KUBECONFIG=<kubeconfig_1>;<kubeconfig_2>;<kubeconfig_n>
```
5. **List all the context**.
```
 kubectl config get-contexts
```

6. Use kubectl command to **switch from one context to others**.
```
 kubectl config use-context <context>
```
  
7. From now on you can **use kubectl to control the specified cluster**. Verify it works. From your laptop, run   
```
 kubectl get nodes
```   

- - - -
### Install the Kubernetes Dashboard

1. On master node, run
```
 kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.2.0/aio/deploy/recommended.yaml
```
2. Then, you can access from external cluster machine with kubectl proxy.
```
 kubectl proxy
```
3. Open browser at http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/pod?namespace=default
4. Configure authorization and authentication following this [guide](https://www.replex.io/blog/how-to-install-access-and-add-heapster-metrics-to-the-kubernetes-dashboard)

- - - -
### Prepare the Persistent Volumes
*This particular setup is specifically to my 2-node cluster where I create 4 PV on worker node and 4 PV on master node. Feel free to adapt to your needs.*  

1. Create the storage class. From your workstation run:
```
 kubectl apply -f storage-class.yaml
```
2. Prepare the directory where the PVs will be hosted. On *master node* run:
```
 sudo mkdir -p /data/volumes/pv1 /data/volumes/pv2 /data/volumes/pv3 /data/volumes/pv4
```
```
 sudo chmod 777 /data/volumes/pv1 /data/volumes/pv2 /data/volumes/pv3 /data/volumes/pv4
```
3. Prepare the directory where the PVs will be hosted. On *worker node* run:
```
 sudo mkdir -p /data/volumes/pv5 /data/volumes/pv6 /data/volumes/pv7 /data/volumes/pv8
```
```
 sudo chmod 777 /data/volumes/pv5 /data/volumes/pv6 /data/volumes/pv7 /data/volumes/pv8
```
4. Create the Persistent Volumes:
```
 kubectl apply -f persistent-volumes.yaml
```

<br> 

***
Author: [Lorenzo Piazza](https://github.com/LorenzoPiazza)
