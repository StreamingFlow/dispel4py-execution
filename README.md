![Laminar Logo](logo.webp)
# Laminar Execution Instructions

The following instructions will allow you to run the Flask application which executes dispel4py workflows 

# Docker
Clone repository 
```
git clone https://github.com/StreamingFlow/dispel4py-execution.git
```
Then enter directory by
```
cd dispel4py-execution 
```

Run docker compose to load up the execution engine and redis server. The first time we recommend to use --build flag.
```
docker compose up --build
```
Next time you could use:
```
docker compose up
```

If you need to rebuild the Docker containers (for instance, after making configuration changes), you can do so by following these steps:

First, bring down the running containers:
```
docker-compose down
```
Then, rebuild and start the containers:
```
docker-compose up --build
```
By following these steps, you can ensure that the execution engine is properly configured and running efficiently.


# Without Docker

Clone repository 
```
git clone https://github.com/Laminar-2/dispel4py-execution.git
```
Then enter directory by
```
cd dispel4py-execution 
```
In order to run the application you need to create a new Python 3.10 enviroment
```
--note conda must be installed beforehand, go to https://conda.io/projects/conda/en/stable/user-guide/install/linux.html
conda create --name py10 python=3.10
conda activate py10
```
Install app modules
```
pip install -r requirements_app.txt
```
Run application
```
python app.py
```

## Other Laminar components

The [laminar client](https://github.com/StreamingFlow/dispel4py-client) offers a user-friendly interface for registering and managing Processing Elements (PEs) as well as stream-based dispel4py workflows. For detailed guidance on how to interact with the system, please refer to the [user manual](https://github.com/StreamingFlow/dispel4py-client/wiki) available on the project's wiki.

In addition, [laminar server](https://github.com/StreamingFlow/dispel4py-server) is another essential component that must be installed and running, either locally or remotely. The server acts as the central hub for managing communication and coordination between the client and the execution engine. It also communicates with the registry, which stores, workflows, PEs, and other essential metadata.
