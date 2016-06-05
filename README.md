# Hierarchical Executor

## Dependencies
```
python 2.7
pip
pip install requests
pip install boto3
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
  [GET]    /api/messages
  [PUT]    /api/topology
  [PUT]    /api/vm/capacity
  [PUT]    /api/tier
```
## API Description
### [GET] /api/messages
Shows the current state of message gathering.
### [PUT] /api/vm/capacity
Executes the plan by deleting, creating and updating containers. Example payload:
```
{
  "capacity": 1
}
```
`curl -X PUT -d @tests/capacity.json localhost:8000/api/vm/capacity`
### [PUT] /api/tier
Create / Delete / Update containers
```
{
  "vm": "i-f9d53956",
  "app": "rubis",
  "name": "app_server",
  "cpu_cores": 1,
  "mem_units": 1
}
```
`curl -X PUT -d @tests/tier.json localhsot:8000/api/tier`

To delete container you need specify cpu_cores = 0. 