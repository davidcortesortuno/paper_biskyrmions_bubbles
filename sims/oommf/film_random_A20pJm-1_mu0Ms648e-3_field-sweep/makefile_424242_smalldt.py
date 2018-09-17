import glob
import os
import re
import subprocess


OMFS = glob.glob('../film_random_A20pJm-2_mu0Ms648e-3/*.omf')

for OMF in OMFS:
    OMFNAME = os.path.basename(OMF)
    SEED = re.search('(?<=rseed)\d+(?=-)', OMFNAME).group(0)
    SAVE_FOLDER = 'film_random_rseed{}_field-sweep_omfs_smallDT'.format(SEED)

    if SEED == '424242':

        # Make folder to save omf files
        if os.path.exists(SAVE_FOLDER):
            os.rmdir(SAVE_FOLDER)
        os.mkdir(SAVE_FOLDER)

        subprocess.call(('oommf boxsi -threads 8 '
                         '-parameters '
                         '"'
                         'OMFFILE {0} '
                         'Bsteps 60 '
                         'BASENAME '
                         '{1}/oommf_film_random_rseed{2}_field-sweep'
                         '" '
                         'oommf_film_random.mif').format(OMF, SAVE_FOLDER, SEED),
                        shell=True)

    else:
        continue
