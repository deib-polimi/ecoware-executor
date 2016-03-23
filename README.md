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
  [POST]   /api/run/tier_hooks
```
## API Description
### [PUT] /api/topology
Example of input payload:
```
{
  "cpu_cores": 8,
  "mem_units": 64,
  "auto_scaling_group": "monolithic-ex-8cpu",
  "hooks_git": "https://github.com/n43jl/hooks",
  "tiers": [
    {
      "name": "pwitter-web",
      "image": "pwitter-web",
      "docker_params": "-p 8080:5000 --add-host=\"db:172.31.31.123\"",
      "entrypoint_params": "-w 3 -k eventlet",
      "tier_hooks": ["test_tier_hook.sh"],
      "depends_on": ["rubiss-jboss"],
      "scale_hooks": ["test_scale_hook.sh"]
    }, {
      "name": "rubis-jboss",
      "image": "polimi/rubis-jboss:nosensors",
      "docker_params": "-p 80:8080 --add-host=\"db:172.31.31.123\"",
      "entrypoint_params": " /opt/jboss-4.2.2.GA/bin/run.sh --host=0.0.0.0 --bootdir=/opt/rubis/rubis-cvs-2008-02-25/Servlets_Hibernate -c default"
    }
  ]
} 
```
Hooks git repository should contain 2 folders: `scale_hooks` and `tier_hooks` with executable hooks inside.

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

### [POST] /api/run/tier_hooks
Run the tier hooks for specified tiers. The tier hooks list to run is specified in topology[TIER_NAME]["tier_hooks"]
```
["pwitter-web", "rubbis-jboss"]
```