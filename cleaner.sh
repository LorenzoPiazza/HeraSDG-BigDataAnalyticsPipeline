#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage ./cleaner.sh <hdfs-shell-pod>";
    exit 1;
fi

echo "================================================================================="
echo "Deleting all the contents from HDFS..."
kubectl exec "$1" -- bash -c "hadoop fs -ls / && /
    hadoop fs -rm -r -skipTrash /HeraSDG /tmp && /
    hadoop fs -ls /"

echo ""
echo "Recreating the empty directories..."
kubectl exec "$1" -- bash -c "hadoop fs -mkdir -p /HeraSDG/raw_data /HeraSDG/clean_data && /
    hadoop fs -chown HeraSDG /HeraSDG && /
    hadoop fs -chmod -R 777 / && /
    hadoop fs -ls /"

echo "================================================================================="
echo "Deleting all the Kakfa messages from topics 'utenti', 'comportamenti', 'premi'..."
echo "...setting the topics retention.ms time to 500ms"
kubectl exec svc/my-kafka -- kafka-configs.sh --bootstrap-server localhost:9092 --alter --topic utenti        --add-config retention.ms=500 
kubectl exec svc/my-kafka -- kafka-configs.sh --bootstrap-server localhost:9092 --alter --topic comportamenti --add-config retention.ms=500 
kubectl exec svc/my-kafka -- kafka-configs.sh --bootstrap-server localhost:9092 --alter --topic premi         --add-config retention.ms=500 
sleep 1
echo "...restoring the retention.ms time to 1 hour"
kubectl exec svc/my-kafka -- kafka-configs.sh --bootstrap-server localhost:9092 --alter --topic utenti        --add-config retention.ms=3600000
kubectl exec svc/my-kafka -- kafka-configs.sh --bootstrap-server localhost:9092 --alter --topic comportamenti --add-config retention.ms=3600000
kubectl exec svc/my-kafka -- kafka-configs.sh --bootstrap-server localhost:9092 --alter --topic premi         --add-config retention.ms=3600000