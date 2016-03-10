# Executor agent
API for managing docker containers
## API
```
  [GET]    /api/allocation
  [GET]    /api/inspect
  [PUT]    /api/topology
  [POST]   /api/container/new
  [PUT]    /api/containers
  [DELETE] /api/container/${container_name}
```
## API Description
### [GET] /api/allocation
Doesn't take input parameters and returns current allocation of docker containers. If method is called without updating or creating containers, then returns {}.
### [GET] /api/inspect
Doesn't take input parameters and returns the result of "docker inspect" command for all running containers.
### [PUT] /api/topology
Example of input payload:
```
{
  "cpu_cores": 8
}
```
Knowing of VM cpu_cores needed to manage "cpuset" array correctly for each docker container.
### [POST] /api/container/new
Method for creating new container. Payload is
```
{
  "name": "pwitter-web",
  "image": "nginx",
  "cpu_cores": 3,
  "mem_units": 1,
  "docker_params": "-p 80:8080 --add-host=\"db:172.31.18.15\"",
  "entrypoint_params": "/opt/jboss-4.2.2.GA/bin/run.sh --host=0.0.0.0 --bootdir=/opt/"
}
```
`docker_params` and `entrypoint_params` are optional.
This method runs command
```
docker run -itd ${docker_params} --cpuset=${cpuset} -m=${mem_mb} --name=${name} ${image} ${entrypoint_params}
```

### [PUT] /api/containers
Example payload:
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