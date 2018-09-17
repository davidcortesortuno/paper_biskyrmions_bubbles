"""

Run simulations by varying Ms and A parameters

Each simulation is a field sweep from 0 to 0.3 T in 6 steps, i.e in steps of
0.5 T

"""

# import glob
# import re
import subprocess
import os
import numpy as np
import textwrap


def SIM_TXT(Ms, A, BzMax, SAVE_FOLDER):

    pre = textwrap.dedent("""\
    #!/bin/bash

    #SBATCH --ntasks-per-node=20    # Tasks per node
    #SBATCH --nodes=1               # Number of nodes requested
    #SBATCH --time=02-00:00:00      # walltime

    """)

    sim = ('tclsh /scratch/dic1v17/miniconda3/pkgs/oommf-2.0a0_20170929a0-5/opt/oommf/oommf.tcl '
           ' boxsi -threads 20 '
           '-parameters '
           '"'
           'Ms {0} '
           'A {1:.0f}e-12 '
           'Bz {2}e-3 '
           'BASENAME '
           '{3}/m_Bz{2:03d}mT'
           '" '
           'oommf_bubble_lattice.mif').format(Ms,
                                              A,
                                              int(BzMax),
                                              SAVE_FOLDER)
    return pre + sim

# Test:
# SAVE_FOLDER = 'omfs_mu0Ms_{:04.0f}mT_A_{:02.0f}pJm-1'.format(0.4 * 1000, 10.)
# print(SIM_TXT(0.4, 10., 300, SAVE_FOLDER))

for Ms in np.arange(0.4, 0.7, 0.05):

    for A in [10., 15., 20., 25., 30., 35.]:

        # Make folder to save omf files
        SAVE_FOLDER = 'omfs_mu0Ms_{:04.0f}mT_A_{:02.0f}pJm-1'.format(Ms * 1000,
                                                                     A)
        if os.path.exists(SAVE_FOLDER):
            os.rmdir(SAVE_FOLDER)
        os.mkdir(SAVE_FOLDER)

        for Bz in np.arange(0, 301, 50):

            F = open('submit', 'w')
            F.write(SIM_TXT(Ms, A, Bz, SAVE_FOLDER))
            F.close()

            subprocess.call('sbatch submit', shell=True)
