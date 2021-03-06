import json
import argparse, os
import math
import subprocess
import shutil
import sys 

cmd = """#!/bin/bash
# Job Name and Files (also --job-name)
#SBATCH -J LIKWID
#Output and error (also --output, --error):
#SBATCH -o node-{1}.out
#SBATCH -e node-{1}.e
#Initial working directory (also --chdir):
#SBATCH -D ./
#Notification and type
#SBATCH --mail-type=END
#SBATCH --mail-user=munch@lnm.mw.tum.de
# Wall clock limit:
#SBATCH --time=0:30:00
#SBATCH --no-requeue
#Setup of execution environment
#SBATCH --export=NONE
#SBATCH --get-user-env
#SBATCH --account=pr83te
#
## #SBATCH --switches=4@24:00:00
#SBATCH --partition={2}
#Number of nodes and MPI tasks per node:
#SBATCH --nodes={0}
#SBATCH --ntasks-per-node=48
#SBATCH --cpus-per-task=1

#module list

#source ~/.bashrc
# lscpu

module unload mkl mpi.intel intel
module load intel/19.0 mkl/2019
module load gcc/9
module unload mpi.intel
module load mpi.intel/2019_gcc
module load cmake
module load slurm_setup

pwd

array=($(ls node{1}/*.json))

mpirun -np {3} ./vlasov_poisson \"${{array[@]}}\"
"""

def run_instance(dim_x, dim_v, degree, n, c):
    with open(os.path.dirname(os.path.abspath(__file__)) + "/tokamak_weak.json", 'r') as f:
       datastore = json.load(f)

    N = {"1":[8,6],"2":[16,6],"4":[32,6],"8":[64,6],"16":[64,12],"32":[64,24],"64":[64,48],"128":[128,48],"256":[256,48],"512":[512,48], "1024":[512,96], "2048":[512, 192]}

    NN = N[str(n)]

    # make modifications
    datastore["General"]["DimX"]       = dim_x
    datastore["General"]["DimV"]       = dim_v
    datastore["General"]["DegreeX"]    = degree
    datastore["General"]["DegreeV"]    = degree
    datastore["General"]["PartitionX"] = NN[0]
    datastore["General"]["PartitionV"] = NN[1]

    datastore["Case"]["NRefinementsX"]       = c/2 + c%2
    datastore["Case"]["NRefinementsV"]       = c/2
    
    # write data to output file
    with open("node%s/inputs%s.json" % (str(n).zfill(4), str(c).zfill(2)), 'w') as f:
        json.dump(datastore, f, indent=4, separators=(',', ': '))

def main():
    # parameters
    dim_x  = 3;
    dim_v  = 3;
    degree = 3;
    shift  = 3; # start with 30*32*(2**3)**3 cells, e.g., 2.0133e9 dofs

    folder_name = "torus-weak-%s-%s-%s" %(str(dim_x), str(dim_v), str(degree) )

    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    os.chdir(folder_name)

    shutil.copy("../../vlasov_poisson", ".")

    #for c, n in enumerate([1, 8, 64, 512]):
    for c, n in enumerate([2, 16, 128, 1024]):

        if not os.path.exists("node%s" % (str(n).zfill(4))):
            os.mkdir("node%s" % (str(n).zfill(4)))

        label = ""
        if n <= 16:
            label = "test"
        elif n <= 768:
            label = "general"
        elif n <= 3072:
            label = "large"

        with open("node%s.cmd" % (str(n).zfill(4)), 'w') as f:
            f.write(cmd.format(str(n), str(n).zfill(4), label, 48*n))
        
        print n

        run_instance(dim_x, dim_v, degree, n, c + shift)

if __name__== "__main__":
  main()

