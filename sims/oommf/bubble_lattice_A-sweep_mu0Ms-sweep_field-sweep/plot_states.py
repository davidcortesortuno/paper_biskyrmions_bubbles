import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import glob
import os
import re
import sys
plt.style.use('../../../notebook/styles/lato_style.mplstyle')
sys.path.append('../../../')
import oommf_tools as ot
import tqdm

# -----------------------------------------------------------------------------

# Create a OOMMFDataRead class object. We will reuse the coordinates
_file = 'm_Bz050mT-Oxs_MinDriver-Magnetization-00-0016933.omf'
omf_file = ot.OOMMFDataRead(_file)
omf_file.set_coordinates()

xs, ys, zs = (np.unique(omf_file.x),
              np.unique(omf_file.y),
              np.unique(omf_file.z)
              )
dx = xs[1] - xs[0]
dy = ys[1] - ys[0]

# Layer to be plotted (here we use the centre slice)
z_index = 20
z_filter = omf_file.z == zs[z_index]
# Filter for the arrows in the plots
arr_fltr_tmp = np.zeros(len(xs))
arr_fltr_tmp[::5] = 1
arr_fltr = np.zeros_like(omf_file.x[z_filter]).reshape(len(xs), -1)
arr_fltr[::5] = arr_fltr_tmp
arr_fltr = arr_fltr.astype(np.bool).reshape(-1,)

# -----------------------------------------------------------------------------

if not os.path.exists('pngs'):
    os.mkdir('pngs')

folder_list = glob.glob('omfs*')
print('FOLDERS:')
print('\n'.join(folder_list))

for FOLDER in tqdm.tqdm(folder_list, desc='Parameters'):
    # print(FOLDER)

    pngs_folder = 'pngs/{}'.format(FOLDER[5:])

    if not os.path.exists(pngs_folder):
        os.mkdir(pngs_folder)

    file_list = glob.glob(os.path.join(FOLDER, '*.omf'))

    for FILE in tqdm.tqdm(file_list, desc='Fields'):

        basename = re.search('m_.*(?=-Oxs)', FILE).group(0)
        # print(basename)

        # Check if PNG file already exists
        if os.path.exists('{}/{}.png'.format(pngs_folder, basename)):
            continue

        omf_file.input_file = FILE
        omf_file.read_m()
        rgb_map = ot.generate_colours(np.column_stack((omf_file.mx,
                                                       omf_file.my,
                                                       omf_file.mz)))

        f, ax = plt.subplots(ncols=1, figsize=(12, 12))

        ax.imshow(rgb_map[z_filter].reshape(len(xs), -1, 3),
                  extent=[(xs.min() - dx * 0.5), (xs.max() + dx * 0.5),
                          (ys.min() - dx * 0.5), (ys.max() + dx * 0.5),
                          ],
                  origin='lower'
                  )

        ax.quiver(omf_file.x[z_filter][arr_fltr],
                  omf_file.y[z_filter][arr_fltr],
                  omf_file.mx[z_filter][arr_fltr],
                  omf_file.my[z_filter][arr_fltr],
                  scale_units='xy', angles='xy', scale=0.05
                  )

        plt.savefig('{}/{}.png'.format(pngs_folder, basename),
                    dpi=150, bbox_inches='tight')
        plt.close()

# -----------------------------------------------------------------------------
# PLOT

# f, ax = plt.subplots(ncols=1, figsize=(12, 12))
# z_index = 20
# z_filter = omf_file.z == zs[z_index]
# 
# ax.imshow(rgb_map[z_filter].reshape(len(xs), -1, 3),
#           extent=[(xs.min() - dx * 0.5), (xs.max() + dx * 0.5),
#                   (ys.min() - dx * 0.5), (ys.max() + dx * 0.5),
#                   ],
#           origin='lower'
#           )
# 
# # Arrows filter
# arr_fltr_tmp = np.zeros(len(xs))
# arr_fltr_tmp[::5] = 1
# arr_fltr = np.zeros_like(omf_file.x[z_filter]).reshape(len(xs), -1)
# arr_fltr[::5] = arr_fltr_tmp
# arr_fltr = arr_fltr.astype(np.bool).reshape(-1,)
# 
# ax.quiver(omf_file.x[z_filter][arr_fltr], omf_file.y[z_filter][arr_fltr],
#           omf_file.mx[z_filter][arr_fltr], omf_file.my[z_filter][arr_fltr],
#           scale_units='xy', angles='xy', scale=0.05
#           )
# plt.show()
# 
# # plt.savefig('oommf_bubble_measure.jpg', dpi=300, bbox_inches='tight')
