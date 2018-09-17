import glob
import os
import re
import subprocess
import numpy as np

for L in [600, 800, 1000, 1200, 1400]:

    # Make folder to save omf files
    SAVE_FOLDER = 'omfs_L{}nm_t200nm'.format(L)
    if os.path.exists(SAVE_FOLDER):
        os.rmdir(SAVE_FOLDER)
    os.mkdir(SAVE_FOLDER)

    # for Bz in np.arange(0.05, 0.26, 0.01):
    for Bz in np.arange(40, 331, 10):

        subprocess.call(('oommf boxsi -threads 6 '
                         '-parameters '
                         '"'
                         'Lx {0}e-9 '
                         'Ly {0}e-9 '
                         'Lz 200e-9 '
                         'Bz {1}e-3 '
                         'BASENAME '
                         '{2}/typeII_bubble_Bz{1:03d}mT_field-sweep'
                         '" '
                         'oommf_isolated_typeII_bubble.mif').format(int(L),
                                                                    int(Bz),
                                                                    SAVE_FOLDER),
                        shell=True)
