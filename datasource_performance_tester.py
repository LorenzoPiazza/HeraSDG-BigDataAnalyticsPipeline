import subprocess

if __name__ == "__main__":
    command = ["python", "data_source.py", "137.204.57.224:30001", "1000", "&"]
    result_file = open( './test.csv', 'a')
    for i in range(10):
        subprocess.run(command,  stdout = result_file)

import multiprocessing
import os                                                               
 
# Creating the tuple of all the processes
all_processes = ('script_A.py', 'script_B.py', 'script_C.py', 'script_D.py')                                    
                                                  
# This block of code enables us to call the script from command line.                                                                                
def execute(process):                                                             
    os.system(f'python {process}')                                       
                                                                                
                                                                                
process_pool = multiprocessing.Pool(processes = 4)                                                        
process_pool.map(execute, all_processes)