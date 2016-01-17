# SETS
# set of all the Tiers (applications)
set Tier; 

# set of all the VM (virtual machines)
set VM;


# PARAMS
# if Tier[i] is already using VM[j]
param tier_used{Tier, VM}; 

# if VM[j] is already used
param vm_used{VM};

# CPU demand for Tiers
param cpu_demand{Tier};

# RAM demand for Tiers
param mem_demand{Tier};

# CPU availability of VM[j]
param cpu_max{VM};

# RAM availability of VM[j]
param mem_max{VM};

# weight for container create / set (usage of tier on VM)
param use_tier_weight{Tier, VM};

# weight for VM create / use (usage of VM)
param use_vm_weight{VM};

# weight for not using container (delete container on VM)
param not_use_tier_weight{Tier, VM};

# weight for not using VM (delete vm)
param not_use_vm_weight{VM};

# VARS
var tier_usage{Tier, VM} >= 0 binary;
var vm_usage{VM} >= 0 binary;
# opposite to tier_usage
var tier_idle{Tier, VM} >= 0 binary;
# opposite to vm_usage
var vm_idle{VM} >= 0 binary;

# Number of CPU Tier[i] uses in VM[j]
var cpu{Tier, VM} >= 0 integer;
# RAM in units Tier[i] uses in VM[j]
var mem{Tier, VM} >= 0 integer; 


# OBJECTIVE FUNCTION
minimize cost:
  sum{i in Tier, j in VM} (use_tier_weight[i, j] * tier_usage[i, j] + not_use_tier_weight[i, j] * tier_idle[i, j]) + sum{j in VM} (use_vm_weight[j] * vm_usage[j] + not_use_vm_weight[j] * vm_idle[j]);


# CONSTRAINTS
# availability for CPU and activation of vm_usage
subject to CPU_availability{j in VM}:
  sum{i in Tier} cpu[i, j] <= cpu_max[j] * vm_usage[j];

# availability for RAM
subject to RAM_availability{j in VM}:
  sum{i in Tier} mem[i, j] <= mem_max[j];

subject to CPU_demand{i in Tier}:
  sum{j in VM} cpu[i, j] >= cpu_demand[i];

subject to RAM_demand{i in Tier}:
  sum{j in VM} mem[i, j] >= mem_demand[i];

subject to CPU_activation{i in Tier, j in VM}:
  cpu_max[j] * tier_usage[i, j] >= cpu[i, j];

subject to RAM_activation{i in Tier, j in VM}:
  mem_max[j] * tier_usage[i, j] >= mem[i, j];

# not allow usage of RAM, but 0 usage of CPU
subject to CPU_RAM_activation{i in Tier, j in VM}:
  cpu_max[j] * cpu[i, j] >= mem[i, j];

# not allow usage of CPU, but 0 usage of RAM
subject to RAM_CPU_activation{i in Tier, j in VM}:
  mem_max[j] * mem[i, j] >= cpu[i, j];

# link tier_idle to tier_usage
subject to link_tier_idle{i in Tier, j in VM}:
  tier_idle[i, j] + tier_usage[i, j] = 1;

# link tier_idle to tier_usage
subject to link_vm_idle{j in VM}:
  vm_idle[j] + vm_usage[j] = 1;

