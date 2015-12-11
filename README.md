# Executor

Implements the "Execute" part of the MAPE (Monitor Analyze Plan Execute) model.
It gets plan from the RabbitMQ, translates it to control instructions for the virtual machines and docker containers, and executes them.

## Installation
To run it you need to install python modules and [ortools](https://pypi.python.org/pypi/ortools) linear solver:
<code>
  pip install python-constraint
  pip install enum
  wget https://pypi.python.org/packages/2.7/o/ortools/ortools-2.3393-py2.7-linux-x86_64.egg#md5=24197ea0616e7c61bd41d5b70f3e2e7d
  easy_install ortools-2.3393-py2.7-linux-x86_64.egg
</code>