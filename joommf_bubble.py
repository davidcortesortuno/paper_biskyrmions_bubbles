import oommfc as oc
import discretisedfield as df
import numpy as np
import matplotlib.pyplot as plt

import colorsys
plt.style.use('styles/lato_style.mplstyle')
mu0 = 4 * np.pi * 1e-7


def convert_to_RGB(hls_color):
    return np.array(colorsys.hls_to_rgb(hls_color[0] / (2 * np.pi),
                                        hls_color[1],
                                        hls_color[2]))


def generate_RGBs(field_data):
    """
    field_data      ::  (n, 3) array
    """
    hls = np.ones_like(field_data)
    hls[:, 0] = np.arctan2(field_data[:, 1],
                           field_data[:, 0]
                           )
    hls[:, 0][hls[:, 0] < 0] = hls[:, 0][hls[:, 0] < 0] + 2 * np.pi
    hls[:, 1] = 0.5 * (field_data[:, 2] + 1)
    rgbs = np.apply_along_axis(convert_to_RGB, 1, hls)

    # Redefine colours less than zero
    # rgbs[rgbs < 0] += 2 * np.pi

    return rgbs


# def init_dot(pos):
# 
#     x, y = pos[0], pos[1]
#     r = np.sqrt(x ** 2 + y ** 2)
# 
#     if r < R:
#         mz = -1
#     else:
#         mz = 1
# 
#     return (0, 0, mz)


def init_type2bubble_bls_II(pos, R=80e-9):
    """
    Initial state to obtain a type II bubble
    We set a Bloch-like skyrmion profile across the sample thickness
    """

    x, y = pos[0], pos[1]
    r = np.sqrt(x ** 2 + y ** 2)
    phi = np.arctan2(y, x)
    phi_b = np.arctan2(y, x) + 0.5 * np.pi

    k = np.pi / R

    if r < R and y > 0:
        m = (np.sin(k * r) * np.cos(phi_b),
             np.sin(k * r) * np.sin(phi_b),
             -np.cos(k * r))
    elif r < R and y < 0:
        m = (-np.sin(k * r) * np.cos(phi_b),
             -np.sin(k * r) * np.sin(phi_b),
             -np.cos(k * r))
    else:
        m = (0, 0, 1)

    return m


class IsolatedBubble(object):
    """
    Class to simulate a bubble using JOOMMF

    Parameters:

        A                   :: exchange (J m^-1)
        Ms                  :: saturation magnetisation (A / m)
        B                   :: applied field (Telsa)
        L                   :: cuboid side length
        thickness           :: cuboid thickness
        init_state_radius   :: initial state radius
        cell                :: discretisation cell lengths
    """

    def __init__(self, A=20e-12, Ms=0.648, B=0.1,
                 L=400e-9, thickness=100e-9,
                 init_state_radius=80e-9,
                 cell=(4e-9, 4e-9, 4e-9)
                 ):
        self.A = A
        self.Ms = Ms / mu0
        self.Ku = A / 2.3e-16
        self.B = B

        self.L = L
        self.thickness = thickness

        print('Exch length lex = ',
              1e9 * np.sqrt(2 * self.A / (mu0 * self.Ms ** 2)),
              'nm'
              )

        self.mesh = oc.Mesh(p1=(-self.L/2, -self.L/2, -self.thickness/2),
                            p2=(self.L/2, self.L/2, self.thickness/2),
                            cell=cell)

        self.system = oc.System(name='oommf_typeII_bubble')
        # Add interactions
        self.system.hamiltonian = (oc.Exchange(A=self.A) +
                                   oc.UniaxialAnisotropy(K1=self.Ku,
                                                           u=(0, 0, 1)) +
                                   oc.Demag() +
                                   oc.Zeeman((0, 0, self.B / mu0))
                                   )

        self.system.m = df.Field(self.mesh,
                                 value=lambda r: init_type2bubble_bls_II(r, init_state_radius),
                                 norm=self.Ms)
        # self.system.m = df.Field(self.mesh, value=(0, 0.1, 0.99),
        #                          norm=self.Ms)

        self.md = oc.MinDriver()

        # Get system cordinates
        self.coordinates = np.array(list(self.system.m.mesh.coordinates))

        # Turn coordinates into a (N, 3) array and save in corresponding
        # variables scaled in nm
        self.x, self.y, self.z = (self.coordinates[:, 0] * 1e9,
                                  self.coordinates[:, 1] * 1e9,
                                  self.coordinates[:, 2] * 1e9
                                  )

        # Array with uniue z coordinates
        self.xs = np.unique(self.x)
        self.ys = np.unique(self.y)
        self.zs = np.unique(self.z)

        self.z_layers = {}
        for i, z in enumerate(self.zs):
            self.z_layers[i] = '{:.2f} nm'.format(z)

        # Compute the initial magnetisation profile
        self.compute_magnetisation()

    def minimise_energy(self):
        self.md.drive(self.system)

        # Update the agnetisation arrays
        self.compute_magnetisation()

    def plot_state(self, size=8, n_arrows=40):
        fig = plt.figure(figsize=(size, size))
        ax = fig.add_subplot(111)

        self.system.m.z.imshow("z", ax=ax)
        self.system.m.quiver("z", ax=ax, n=(n_arrows, n_arrows))

    def compute_magnetisation(self):
        # phi_oommf = np.arctan2(y_oommf, x_oommf)
        # Get the magnetisation for every coordinate in the magnetisation list
        values = []
        for c in self.coordinates:
            values.append(self.system.m(c))
        values = np.array(values)

        # Save them in the corresponding row and column of the m list
        # mx, my, mz:
        self.mx, self.my, self.mz = (values[:, 0] / self.Ms,
                                     values[:, 1] / self.Ms,
                                     values[:, 2] / self.Ms)

        # mphi = lambda z_i: (-mx_O * np.sin(phi_O) + my_O * np.cos(phi_O))[_filter_y_O(z_i)]
        # mr = lambda z_i: (mx_O * np.cos(phi_O) + my_O * np.sin(phi_O))[_filter_y_O(z_i)]

    def plot_slice(self, n_slice=0, arrow_stride=7):
        """
        """
        print('Plotting for slice at z =', self.zs[n_slice], 'nm')
        z_filter = self.z == np.unique(self.zs)[n_slice]

        f, ax = plt.subplots(ncols=1, figsize=(8, 8))

        rgb_map = generate_RGBs(np.column_stack((self.mx[z_filter],
                                                 self.my[z_filter],
                                                 self.mz[z_filter])))
        # ax.scatter(self.x[z_filter], self.y[z_filter],
        #            c=rgb_map, marker='s',
        #            # s=20
        #            )
        xmin, xmax = (np.min(self.x[z_filter]) - 0.5 * self.mesh.cell[0] * 1e9,
                      np.max(self.x[z_filter]) + 0.5 * self.mesh.cell[0] * 1e9)
        ymin, ymax = (np.min(self.y[z_filter]) - 0.5 * self.mesh.cell[1] * 1e9,
                      np.max(self.y[z_filter]) + 0.5 * self.mesh.cell[1] * 1e9)
        ax.imshow(rgb_map.reshape(self.mesh.n[0], -1, 3),
                  extent=[xmin, xmax, ymin, ymax]
                  )

        # Filter for the arrows:
        arr_fltr_tmp = np.zeros(len(self.xs))
        arr_fltr_tmp[::arrow_stride] = 1
        arr_fltr = np.zeros_like(self.x[z_filter]).reshape(len(self.xs), -1)
        arr_fltr[::arrow_stride] = arr_fltr_tmp
        arr_fltr = arr_fltr.astype(np.bool).reshape(-1,)

        ax.quiver(self.x[z_filter][arr_fltr],
                  self.y[z_filter][arr_fltr],
                  self.mx[z_filter][arr_fltr],
                  self.my[z_filter][arr_fltr],
                  # scale=None
                  scale_units='xy', angles='xy', scale=0.1
                  )

        plt.show()

    def save_data(self, filename='type_II_bubble'):

        self.compute_magnetisation()

        np.savetxt('{}_coordinates.txt'.format(filename), self.coordinates)

        np.savetxt('{}_mx.txt'.format(filename), self.mx)
        np.savetxt('{}_my.txt'.format(filename), self.my)
        np.savetxt('{}_mz.txt'.format(filename), self.mz)
