### preprocessor.py

### This is the preprocessor component.
### It a Apache Beam Pipeline to read data from hdfs, process them and store again on Hdfs.
### The pipeline work is delegated to Apache Spark. 

# Using the Apache Spark Runner(https://beam.apache.org/documentation/runners/spark/)
# 1. Start a Spark cluster which exposes the master on port 7077 by default.
# 2. Start JobService that will connect with the Spark master:
#    with Docker (preferred): docker run --net=host apache/beam_spark_job_server:latest --spark-master-url=spark://localhost:7077
#    or from Beam source code: ./gradlew :runners:spark:job-server:runShadow -PsparkMasterUrl=spark://localhost:7077
# 3. Submit the pipeline through the pipeline options. Note however that environment_type=LOOPBACK is only intended for local testing. See here for details.

import subprocess
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import time

if __name__ == "__main__":
    # result = subprocess.run(["ls", "-l"])
  
    print("Hi Lorenzo!")
    # time.sleep(360)
    # Get the Spark master endpoint in the K8s cluster
    # spark_master_endpoint = "spark://my-spark-master-0.my-spark-headless.default.svc.cluster.local:7077"
    # spark_master_endpoint = "my-spark-master-svc:7077"
    
    
    # Create the PipelineOptions
    options = PipelineOptions([
    "--runner=PortableRunner",          #Portable Runner is needed to execute a Python Apache Beam pipeline on Spark
    "--job_endpoint=localhost:8099",    #The job endpoint is the JobService, so the central instance where you submit your Beam pipeline. The JobService will create a Spark job for the pipeline and execute the job.
    # "--environment_type=LOOPBACK",
    # "--hdfs_host=my-hdfs-namenodes",
    # "--hdfs_port=8020",
    # "--hdfs_user=lori"
    ])
    with beam.Pipeline(options=options) as p:
        output = (
            p
            | 'Create mock values' >> beam.Create([1,2,3,4,5,6])
            | 'Sum all values' >> beam.CombineGlobally(sum)
        )
        output | beam.FlatMap(print)

        # output | beam.io.hadoopfilesystem.HadoopFileSystem._list("hdfs://funziona.txt")
    # hdfs = beam.io.hadoopfilesystem.HadoopFileSystem(options)
    # hdfs.create("hdfs://funziona.txt")
