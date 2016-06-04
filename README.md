# Executor

## Dependencies
```
python 2.7
pip
pip install requests
pip install boto3
wget https://github.com/google/or-tools/releases/download/v2015-09/Google.OrTools.python.examples.3322.tar.gz
tar xvf Google.OrTools.python.examples.3322.tar.gz
cd ortools_examples
python setup.py install
```

## AWS credentials

Add credentials to aws_driver.py:
`os.environ["AWS_SECRET_ACCESS_KEY"] = ""`

## API
```
  [GET]    /api/allocation
  [GET]    /api/inspect
  [GET]    /api/topology
  [PUT]    /api/topology
  [PUT]    /api/emulate
  [PUT]    /api/execute
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

### [PUT] /api/emulate
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