# HOW TO SET UP A K8S CLUSTER

*The following guide is inspired by the official [Creating a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/) guide*

### *Operations to execute on all nodes*

#### A) INSTALL KUBEADM
1. **Disable swap memory on your node.**  
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

2. **Letting iptables see bridged traffic**    
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

3. **Check [required ports](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/#check-required-ports) are open**  
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

4. **Install the Docker Engine**
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

5. **Configure Docker**
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


6. **Install KUBEADM KUBELET E KUBECTL**
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

### *Operations to execute only on master node*

1. **Start the Control Plane**
    ```
    sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-cert-extra-sans=137.204.57.224
    ```
    *Note*:  
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

2. **Follow the instructions on output to configure kubectl using the right kubeconfig file**  
*The kubeconfig file is necessary to instruct kubectl how to connect to the API-Server.*

3. **Deploy a Pod Network (I choose Flannel)**
    ```
    kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
    ```
   
    Watch the Pod status
    ```
    watch kubectl get pods --all-namespaces
    ```
    After some minutes every Pods should be in Running status. And with
    ```
    kubectl cluster-info
    ```
    you should see that both API Server and CoreDNS are running.  

4. **Enable the scheduling of Pods also on Master Node**
    ```
    kubectl taint nodes --all node-role.kubernetes.io/master-
    ```

5. **(Optional): configure kubectl to access the api-server from outside the cluster.**  
	(Prerequisite: Install kubectl on your laptop).  
	5.1 First copy the kubeconfig file from master node to your laptop. On your laptop run:  
	```
	scp -i ~/Downloads/piazzakey ubuntu@137.204.57.224:/home/ubuntu/.kube/config .
	```  
	*Note: modify the command with your ssh options.*  
	5.2 Modify the kubeconfig file on your laptop replacing the internal IP of the API Server with its public IP.
	When we run `kubeadmin init` we have infact add that ip to the 		certified IP list, using the *apiserver-cert-extra-sans* parameter. So, now you can use it.    
	5.3 Verify it works. From your laptop, run   
	```
	kubectl --kubeconfig <kubeconfig_file> get nodes
	```  
	
### *Operations to execute only on WORKER node*
1. **Join the cluster**
    ```
    kubeadm join <master-node-host>:<api-server-port> --token <token> \
        --discovery-token-ca-cert-hash sha256:<hash>
    ```  
    NOTE: You can run `kubeadm token create --print-join-command` in Kubernetes master to get the join command that should be executed in Kubernetes nodes.



