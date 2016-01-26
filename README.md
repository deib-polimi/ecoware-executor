# Executor

Implements the "Execute" part of the MAPE (Monitor Analyze Plan Execute) model.

It has 3 branches: `csp`, `ilp` and `master`.

`csp` and `ilp` gets plan (resource demand for the tiers) as input and search for VM and containers allocation using either "Constraint Satisfiability Problem" solver or "Integer Linear Programming" solver.

`master` doesn't do any allocation, but provide API for creating VM and docker containers on it.

## Run
```
  bash init.sh # database initialization
  python httpHandler.py # run web-server
```

## How to package vagrant VM in box
After packaging vm I got the error `"Warning: Authentication failure. Retrying... "`. To fix it we need some easy manipulations:

1. Put in `Vagrantfile`
    ```
    config.ssh.insert_key = false
    ```

2. Run the VM, ssh to it (password is `vagrant`) and add `vagrant.pub` to `authorise_keys`:
    ```
    vagrant up
    vagrant ssh
    wget https://raw.githubusercontent.com/mitchellh/vagrant/master/keys/vagrant.pub -O .ssh/authorized_keys
    chmod 700 .ssh
    chmod 600 .ssh/authorized_keys
    chown -R vagrant:vagrant .ssh
    exit
    ```

3. Get the VM id from VirtualBox with `vboxmanage list runningvms` and run:
    ```
    vagrant package --base ${HERE_YOUR_ID}
    vagrant destroy
    vagrant box add ${HERE_BOX_NAME} package.box
    rm package.box
    ```

4. Remove this line from `Vagrantfile`
    ```
    config.ssh.insert_key = false
    ```
    
5. Remove `package.box`, add box name in `Vagrantfile` and `vagrant up`!