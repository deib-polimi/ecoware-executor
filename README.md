# Monolithic Executor

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
Location to the credentials is configured in topology: topology.infrastructure.cloud_driver.credentials.
The file format is:
```
AWS_ACCESS_KEY_ID=AAA
AWS_SECRET_ACCESS_KEY=bbbb
```

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
  "infrastructure": {
    "cloud_driver": {
      "autoscaling_groupname": "monolithic-ex-2cpu",
      "credentials": "/ecoware/credentials.conf"
    },
    "hooks_git_repo": "https://github.com/n43jl/hooks",
    "cpu_cores": 2,
    "mem_units": 8
  },
  "apps": [{
    "name": "rubis",
    "tiers": {
      "loadbalancer": {
        "name": "Front LoadBalancer",
        "max_node": 1,
        "docker_image": "nginx",
        "depends_on": ["app_server"],
        "on_dependency_scale": "reload_server_pool.sh"
      }, "app_server": {
        "name": "Application Logic Tier",
        "docker_image": "nginx",
        "depends_on": ["db"],
        "on_node_scale": "jboss_hook.sh",
        "on_dependency_scale": "test_tier_hook.sh",
        "ports": ["8080:80"]
      }, "db": {
        "name": "Data Tier",
        "max_node": 1,
        "docker_image": "nginx",
        "on_node_scale": "mysql_hook.sh",
        "ports": ["8081:80"]
      }

    }
  }, {
    "name": "pwitter",
    "tiers": {
      "app_server": {
        "name": "Application Logic Tier",
        "docker_image": "nginx",
        "ports": ["8082:80"]
      }, "db": {
        "name": "Data Tier",
        "max_node": 1,
        "docker_image": "hello-world",
        "on_node_scale": "mysql_hook.sh",
        "ports": ["3307:3306"]
      }
    }
  }]
}
```
`curl -X PUT -d @tests/topology.json localhost:8000/api/topology`

Hooks git repository should contain 2 folders: `scale_hooks` and `tier_hooks` with executable hooks inside.

### [PUT] /api/translate
Translates plan to the list of actions, without executing them. Example payload:
```
{
    "rubis": {
        "db": {
            "cpu_cores": 7,
            "mem_units": 1
        }, "app_server": {
            "cpu_cores": 1,
            "mem_units": 1
        }
    }
}
```
`curl -X PUT -d @tests/plan.json localhost:8000/api/translate`
### [PUT] /api/execute
Executes the plan by deleting, creating and updating containers. Example payload:
```
{
    "rubis": {
        "db": {
            "cpu_cores": 7,
            "mem_units": 1
        }, "app_server": {
            "cpu_cores": 1,
            "mem_units": 1
        }
    }
}
```
`curl -X PUT -d @tests/plan.json localhost:8000/api/execute`