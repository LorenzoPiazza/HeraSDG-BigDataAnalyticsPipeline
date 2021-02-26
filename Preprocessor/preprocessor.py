### preprocessor.py

### This is the preprocessor component.
### It a Apache Beam Pipeline to read data from hdfs, process them and store again on Hdfs.
### The pipeline work is delegated to Apache Spark. 

# Start a Spark cluster which exposes the master on port 7077 by default.
# Start JobService that will connect with the Spark master:
# with Docker (preferred): docker run --net=host apache/beam_spark_job_server:latest --spark-master-url=spark://localhost:7077
# or from Beam source code: ./gradlew :runners:spark:job-server:runShadow -PsparkMasterUrl=spark://localhost:7077
# Submit the pipeline as above. Note however that environment_type=LOOPBACK is only intended for local testing. See here for details.

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    "--runner=PortableRunner",          #Portable Runner is needed to execute a Python Apache Beam pipeline on Spark
    "--job_endpoint=localhost:8099",    #The job endpoint is the JobService, so the central instance where you submit your Beam pipeline. The JobService will create a Spark job for the pipeline and execute the job.
    "--environment_type=LOOPBACK"
])
with beam.Pipeline(options) as p:
    ...

if __name__ == "__main__":
    print("Hello world!")