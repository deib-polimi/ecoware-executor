# Executor

Implements the "Execute" part of the MAPE (Monitor Analyze Plan Execute) model.
It gets plan from the RabbitMQ, translates it to control instructions for the virtual machines and docker containers, and executes them.

## Installation
<code>
  docker run -it --rm -p 8000:8000 n43jl/executor
</code>