# SETS
# set of all the Tiers
set I; 

# set of all the VM
set J;


# PARAMS
# CPU demand for Tiers
param c{I};

# RAM demand for Tiers
param m{I};

# CPU availability of VM[j]
param c_max{J};

# RAM availability of VM[j]
param m_max{J};

# Price of VM[j]
param p{J};


# VARS
# if Tier[i] uses VM[j]
var z{I, J} >= 0 binary;

# Number of CPU Tier[i] uses in VM[j]
var x{I, J} >= 0 integer;

# RAM in GB Tier[i] uses in VM[j]
var y{I, J} >= 0 integer; 


# OBJECTIVE FUNCTION
minimize cost:
  sum{j in J} p[j] * sum{i in I} z[i, j];


# CONSTRAINTS
subject to CPU_availability{j in J}:
  sum{i in I} x[i, j] <= c_max[j];

subject to RAM_availability{j in J}:
  sum{i in I} y[i, j] <= m_max[j];

subject to CPU_demand{i in I}:
  sum{j in J} x[i, j] = c[i];

subject to RAM_demand{i in I}:
  sum{j in J} y[i, j] = m[i];

subject to CPU_activation{i in I, j in J}:
  c_max[j] * z[i, j] >= x[i, j];

subject to RAM_activation{i in I, j in J}:
  m_max[j] * z[i, j] >= y[i, j];

# not allow usage of RAM, but 0 usage of CPU
subject to CPU_RAM_activation{i in I, j in J}:
  c_max[j] * x[i, j] >= y[i, j];

# not allow usage of CPU, but 0 usage of RAM
subject to RAM_CPU_activation{i in I, j in J}:
  m_max[j] * y[i, j] >= x[i, j];