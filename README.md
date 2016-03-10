# Executor agent
API for managing docker containers
## API
```
  [GET]    /api/allocation
  [GET]    /api/inspect
  [GET]    /api/topology
  [PUT]    /api/topology
  [PUT]    /api/translate
  [PUT]    /api/execute
```
## API Description
### [PUT] /api/topology
Example of input payload:
```
{
  "cpu_cores": 8,
  "mem_units": 32,
  "tiers": [
    {
      "name": "pwitter-web",
      "image": "pwitter-web",
      "docker_params": "-p 8080:5000 --add-host=\"db:172.31.31.123\"",
      "entrypoint_params": "-w 3 -k eventlet"
    }, {
      "name": "rubis-jboss",
      "image": "polimi/rubis-jboss:nosensors",
      "docker_params": "-p 80:8080 --add-host=\"db:172.31.31.123\"",
      "entrypoint_params": " /opt/jboss-4.2.2.GA/bin/run.sh --host=0.0.0.0 --bootdir=/opt/rubis/rubis-cvs-2008-02-25/Servlets_Hibernate -c default"
    }
  ]
}
```

### [PUT] /api/translate
Translates plan to the list of actions, without executing them. Example payload:
```
{
  "rubis-jboss": {
    "cpu_cores": 7,
    "mem_units": 1
  }, "pwitter-web": {
    "cpu_cores": 1,
    "mem_units": 1
  }
}
```
### [PUT] /api/execute
Executes the plan by deleting, creating and updating containers. Example payload:
```
{
  "rubis-jboss": {
    "cpu_cores": 7,
    "mem_units": 1
  }, "pwitter-web": {
    "cpu_cores": 1,
    "mem_units": 1
  }
}
```