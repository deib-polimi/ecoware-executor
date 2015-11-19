# Executor

Implements the "Execute" part of the MAPE (Monitor Analyze Plan Execute) model.
It gets plan from the RabbitMQ, translates it to control instructions for the virtual machines and docker containers, and executes them.

## Installation
To run it you need to install "constraint" python module.
<p><code>pip install python-constraint</code></p>