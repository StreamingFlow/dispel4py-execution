from dispel4py.workflow_graph import WorkflowGraph
from dispel4py.new.simple_process import process_and_return as simple_process_return
from dispel4py.new.simple_process import process as simple_process
from dispel4py.new.multi_process import process as multi_process
from dispel4py.new.processor import STATUS_TERMINATED
from dispel4py.new.dynamic_redis import process as dyn_process
#from dispel4py.new.dynamic_redis_v1 import process as dyn_process
import codecs
#import shutil
import cloudpickle as pickle 
from flask import Flask, request, Response, stream_with_context, jsonify, send_from_directory
from flask_cors import CORS
import importlib
from easydict import EasyDict as edict
from io import StringIO 
from waitress import serve
import pkgutil
import re
import os
import subprocess 
import sys
import configparser
import json
import pathlib
import time
from multiprocessing import Process, Lock, SimpleQueue

def createConfigFile():
    config = configparser.ConfigParser()

    print("Arguments for MULTI configuration")
    num = input("num: ")
    iter = input("iter: ")
    simple = ""
    while simple not in ["y", "n"]:
        simple = input("simple [y/n]: ").lower()
    simple = simple == "y"
    config["MULTI"] = {
        "num": num,
        "iter": iter,
        "simple": simple
    }
    
    print("Arguments for DYNAMIC configuration")
    num = input("num: ")
    iter = input("iter: ")
    simple = ""
    while simple not in ["y", "n"]:
        simple = input("simple [y/n]: ").lower()
    simple = simple == "y"
    redis_ip = input("redis_ip: ")
    redis_port = input("redis_port: ")
    config["DYNAMIC"] = {
        "num": num,
        "iter": iter,
        "simple": simple,
        "redis_ip": redis_ip,
        "redis_port": redis_port
    }

    with open("config.ini", "w") as configfile:
        print("Saving configuration details to config.ini")
        config.write(configfile)

if not os.path.exists('./config.ini'):
    print("Could not find config file - beginning execution engine initialiser")
    createConfigFile()


def install(package):
    if package in sys.modules:
        print(f"{package} is already installed.")
    elif pkgutil.find_loader(package) is not None:
        print(f"{package} is a standard library module.")
    else:
        print(f"Installing package: {package}")
        subprocess.call([sys.executable, "-m", "pip", "install", package])

def import_module(module_name):
    if module_name in sys.modules:
        print(f"{module_name} is already imported.")
    else:
        globals()[module_name] = importlib.import_module(module_name)

def deserialize_directory(data,path):

    if data == None: 
        return None 

    for item, item_data in data.items():

        item_path = os.path.join(path,item)

        if item_data["type"] == "file":

            with open(item_path,"w") as f:
                  file_content = item_data["content"]
                  f.write(file_content)

        elif item_data["type"] == "directory":

            os.makedirs(item_path,exist_ok=True)
            deserialize_directory(item_data["contents"], item_path)


def deserialize(data):
    # Importing the necessary module before deserialization
    return pickle.loads(codecs.decode(data.encode(), "base64"))

app = Flask(__name__)
CORS(app)


@app.route('/resource', methods=['PUT'])
def acquire_resource():
    app.logger.info("---------- Acquiring resources")
    app.logger.info("Request form data: %s", request.form)
    app.logger.info("Request files: %s", request.files)

    user = request.form["user"]
    user_dir = os.path.join("cache", user)
    pathlib.Path(user_dir).mkdir(parents=True, exist_ok=True)

    for file in request.files.getlist("files"):
        app.logger.info("Processing file: %s", file.filename)
        file_path = os.path.join(user_dir, file.filename)
        try:
            with open(file_path, "wb") as f:
                file_content = file.read()
                app.logger.info("File content size: %d bytes", len(file_content))
                f.write(file_content)
            app.logger.info("Saved file to %s", file_path)
        except Exception as e:
            app.logger.error("Error saving file %s: %s", file.filename, str(e))

    return "Success"




@app.route('/run', methods=['GET', 'POST'])
def run_workflow():
    print("Starting workflow")
    #todo check if request is post and error handle each param 
    data = request.get_json()
    

    workflow_id = data["workflowId"]
    workflow = data["graph"]
    inputCode = data["inputCode"]
    process = data["process"]
    resources = data["resources"]
    imports = data["imports"]
    user = data["user"]
    #for handling dynamic imports from the CLI
    module_source_code = data["moduleSourceCode"]
    module_name = data["moduleName"]
    
    import_list = list(filter(None, imports.split(',')))
    
    #todo: fix formatting 

    #handle imports 
    for _import in import_list:
        if _import != "No imports available":
            install(_import)
        #import_module(_import)

    #handle dynamic imports from the CLI
    if module_source_code:
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        mod = importlib.util.module_from_spec(spec)
        exec(module_source_code, mod.__dict__)
        sys.modules[module_name] = mod
        print(f"Module {module_name} imported successfully.")

    if workflow: #checking if user specified graph in registry
        workflow_code = workflow["workflowCode"]
    else:
        workflow_code = data["workflowCode"] #direct code 

    unpickled_workflow_code  = deserialize(workflow_code)
    unpickled_input_code  = deserialize(inputCode)


    graph: WorkflowGraph = unpickled_workflow_code #Code execution 
    nodes = graph.get_contained_objects() #nodes in graph 
    producer = get_first(graph).name # Get first PE in graph

    config = configparser.ConfigParser()
    config.read('config.ini')
    args_dict = {}

    try:
        if process == 2:
            settings = config['MULTI']
            args_dict["num"] = int(settings["num"])
            args_dict["iter"] = int(settings["iter"])
            args_dict["simple"] = settings["simple"] == "True"
        if process == 3:
            settings = config['DYNAMIC']
            args_dict["num"] = int(settings["num"])
            args_dict["iter"] = int(settings["iter"])
            args_dict["simple"] = settings["simple"] == "True"
            args_dict["redis_ip"] = settings["redis_ip"]
            args_dict["redis_port"] = settings["redis_port"]
            
    except:
        if process != 1:
            print("Couldn't read Settings from config file - using default None")
        args_dict = None
    

    return Response(stream_with_context(run_process(process, graph, unpickled_input_code, producer, edict(args_dict), resources, user)), mimetype="application/json")

def acquire_resources(resources: list[str], user: str):
    for resource in resources:
        if not os.path.exists(os.path.join("cache", user, resource)):
            yield resource


def check_resources(resources: list[str], user: str, timeout: int = 60, check_interval: float = 0.5):
    for resource in resources:
        print("Looking for " + resource)
        resource_path = os.path.join("cache", user, resource)
        start_time = time.time()
        while not os.path.exists(resource_path):
            if time.time() - start_time > timeout:
                print(f"Timeout while waiting for {resource}")
                break
            print(f"Not found {resource}: {os.path.exists(resource_path)}")
            time.sleep(check_interval)
        if os.path.exists(resource_path):
            print("Found " + resource)


def run_process(processor_type, graph, producer, producer_name, args_dict, resources, user):
    # First find what resources we don't have
    required_resources = []
    for resource_request in acquire_resources(resources, user):
         required_resources.append(resource_request)
    if len(required_resources) > 0:
        yield json.dumps({"resources": required_resources}) + "\n"
    
    # Then wait for all resources to arrive
    print("Waiting for resources")

    for output in get_process_output(processor_type, graph, producer, producer_name, args_dict, resources, user):
        sys.__stdout__.write(output)
        sys.__stdout__.flush()
        yield output

def get_process_output(processor_type, graph, producer, producer_name, args_dict, resources, user):
    q = SimpleQueue()

    def process_func(processor_type, graph, p, args_dict, user, q:SimpleQueue):
        check_resources(resources, user) # waits for resources to arrive
        buffer = IOToQueue(q)
        pathlib.Path(os.path.join("cache", user)).mkdir(parents=True, exist_ok=True)
        os.chdir(os.path.join("cache", user))
        sys.stdout = buffer
        print(p)
        try:
            if processor_type == 1:
                output = simple_process_return(graph, p)
                q.put({"result": output})
            if processor_type == 2:
                output = multi_process(graph, p, args_dict)
                if output is not None:
                    value = output.get()
                    if value != STATUS_TERMINATED:
                        q.put({"part-result": output})
                    else:
                        q.put({"result": []})
                else:
                    q.put({"result": None})
            if processor_type == 3:
                dyn_process(graph, p, args_dict)
                q.put({"result": None})
        except Exception as e:
            q.put({"error": str(e)})
        finally:
            q.put("END")
            sys.stdout = sys.__stdout__
    print("Before_Process")
    Process(target=process_func, args=(processor_type, graph, {producer_name: producer}, args_dict, user, q)).start()
    
    while True:
        output:dict = q.get()
        if output == "END":
            break
        yield json.dumps(output) + "\n"

class IOToQueue(StringIO):
    def __init__(self, queue:SimpleQueue):
        super()
        self.queue = queue

    def write(self, __s: str) -> int:
        self.queue.put({"response": __s})
        return len(__s)
    
    def read(self, __size: int | None = ...) -> str:
        return self.queue.get()

def get_first(graph: WorkflowGraph):
    id_dict = {}
    
    for x in graph.get_contained_objects():
        correct = True
        for start, end in graph.graph.edges:
            start = start.get_contained_object()
            end = end.get_contained_object()
            if end == x:
                correct = False
        if correct:
            print("Producer - " + str(x))
            return x
        #id = int(re.search(r'\d+', getattr(x,'id')).group())  
        #id_dict[id] = x  

    #min_id = min(id_dict.keys())    
        
    #return id_dict[min_id]  

def main():
    serve(app, host=('127.0.0.1' if os.getenv('EXECUTION_HOST') is None else os.getenv('EXECUTION_HOST')), port='5000')

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    main()

