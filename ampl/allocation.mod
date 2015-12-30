# SETS
# set of all the Tiers
set I; 

# set of all the VM
set J;


# PARAMS
# if Tier[i] used VM[j]
param u{I, J}; 

# CPU demand for Tiers
param c{I};

# RAM demand for Tiers
param m{I};

# CPU availability of VM[j]
param c_max{J};

# RAM availability of VM[j]
param m_max{J};

# Price of VM[j]
# param p{J};


# VARS
# if Tier[i] uses VM[j]
var usage{I, J} >= 0 binary;
var vm_usage{J} >= 0 binary;
var container_delete{I, J} >= 0 binary;
var container_create{I, J} >= 0 binary;
var container_set{I, J} >= 0 binary;

# Number of CPU Tier[i] uses in VM[j]
var cpu{I, J} >= 0 integer;

# RAM in units (1 unit = 0.5GB) Tier[i] uses in VM[j]
var mem{I, J} >= 0 integer; 


# OBJECTIVE FUNCTION
minimize cost:
  sum{j in J, i in I} usage[i, j];


# CONSTRAINTS
subject to CPU_availability{j in J}:
  sum{i in I} cpu[i, j] <= c_max[j];

subject to RAM_availability{j in J}:
  sum{i in I} mem[i, j] <= m_max[j];

subject to CPU_demand{i in I}:
  sum{j in J} cpu[i, j] >= c[i];

subject to RAM_demand{i in I}:
  sum{j in J} mem[i, j] >= m[i];

subject to CPU_activation{i in I, j in J}:
  c_max[j] * usage[i, j] >= cpu[i, j];

subject to RAM_activation{i in I, j in J}:
  m_max[j] * usage[i, j] >= mem[i, j];

# CPU RAM activation
subject to CPU_RAM_activation{i in I, j in J}:
  c_max[j] * cpu[i, j] >= mem[i, j];

# not allow usage of CPU, but 0 usage of RAM
subject to RAM_CPU_activation{i in I, j in J}:
  m_max[j] * mem[i, j] >= cpu[i, j];

