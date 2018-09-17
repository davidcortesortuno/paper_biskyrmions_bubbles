import numpy as np
import re
import colorsys


# -----------------------------------------------------------------------------
# Utilities to generate a HSL colourmap from the magnetisation field data

def convert_to_RGB(hls_color):
    return np.array(colorsys.hls_to_rgb(hls_color[0] / (2 * np.pi),
                                        hls_color[1],
                                        hls_color[2]))


def generate_colours(field_data, colour_model='rgb'):
    """
    field_data      ::  (n, 3) array
    """
    hls = np.ones_like(field_data)
    hls[:, 0] = np.arctan2(field_data[:, 1],
                           field_data[:, 0]
                           )
    hls[:, 0][hls[:, 0] < 0] = hls[:, 0][hls[:, 0] < 0] + 2 * np.pi
    hls[:, 1] = 0.5 * (field_data[:, 2] + 1)

    if colour_model == 'rgb':
        rgbs = np.apply_along_axis(convert_to_RGB, 1, hls)
        return rgbs

    elif colour_model == 'hls':
        return hls

    else:
        raise Exception('Specify a valid colour model: rgb or hls')


# -----------------------------------------------------------------------------


class OOMMFDataRead(object):
    """
    Class to extract the magnetisation field data from an OOMMF file with
    a regular mesh grid (coordinates are generated in this class)
    """

    def __init__(self, input_file):

        self.input_file = input_file
        self.read_header()

    def read_header(self):

        _file = open(self.input_file)

        # Generate a single string with the whole header up to the line where
        # numerical Data starts
        line = _file.readline()
        data = ''
        while not line.startswith('# Begin: Data Text'):
            data += line
            line = _file.readline()

        attrs = {'xstepsize': 'dx',  'ystepsize': 'dy', 'zstepsize': 'dz',
                 'xbase': 'xbase',  'ybase': 'ybase', 'zbase': 'zbase',
                 'xmin': 'xmin', 'ymin': 'ymin', 'zmin': 'zmin',
                 'xmax': 'xmax', 'ymax': 'ymax', 'zmax': 'zmax',
                 }

        # Regex search the attributes. Stepsizes are specified as dx, dy, dz
        for k in attrs.keys():
            num_val = float(re.search('(?<={}: )[0-9\-\.e]+'.format(k),
                            data).group(0))
            setattr(self, attrs[k], num_val)

        # Compute number of elements in each direction
        self.nx = int((self.xmax - self.xmin) / self.dx)
        self.ny = int((self.ymax - self.ymin) / self.dy)
        self.nz = int((self.zmax - self.zmin) / self.dz)

        _file.close()

    def read_m(self):
        data = np.loadtxt(self.input_file)
        Ms = np.sqrt(np.sum(data ** 2, axis=1))
        Ms[Ms == 0.0] = 0.0
        self.mx, self.my, self.mz = (data[:, 0] / Ms,
                                     data[:, 1] / Ms,
                                     data[:, 2] / Ms)

    def set_coordinates(self):
        xs, ys, zs = (np.arange(float(self.nx)),
                      np.arange(float(self.ny)),
                      np.arange(float(self.nz))
                      )
        xs *= self.dx
        xs += self.xbase
        ys *= self.dy
        ys += self.ybase
        zs *= self.dz
        zs += self.zbase

        xs = np.tile(np.tile(xs, self.ny), self.nz)
        ys = np.tile(np.repeat(ys, self.nx), self.nz)
        zs = np.repeat(zs, self.nx * self.ny)

        # int(len(xs), len(ys), len(zs))

        # self.coordinates = np.ravel(np.column_stack((xs, ys, zs))) * 1e9
        self.coordinates = np.column_stack((xs, ys, zs)) * 1e9
        self.x, self.y, self.z = (self.coordinates[:, 0],
                                  self.coordinates[:, 1],
                                  self.coordinates[:, 2])


# -----------------------------------------------------------------------------


class OOMMFODTRead(object):

    """
    Class to read an ODT file from an OOMMF simulation output

    Columns from the ODT table can be obtained calling an element of this class
    from a  valid column name, e.g.

        data = OOMMFODTRead(my_odt_file)
        total_energy = data['Oxs_CGEvolve::Total energy']
    """

    def __init__(self, input_file):

        self.input_file = input_file
        self.read_header()
        # Load the ODT file numerical data
        self.data = np.loadtxt(self.input_file)

    def read_header(self):
        f = open(self.input_file)

        # Read the third line which has the header names
        i = 0
        for i in range(4):
            l = f.readline()
        f.close()
        # Remove the starting "# Columns:" string
        l = l[11:]

        # Separate the header strings:
        # re.split('}\s{|\s\s\s\s|\s{|\sOxs', l)
        header = re.findall(r'Oxs_[A-Za-z\s\:}]+(?=Oxs|{Oxs|\n)', l)
        # Assign the name and column number
        self.columns = {}
        for i, h in enumerate(header):
            h = h.strip()
            h = h.strip('}')
            self.columns[h] = i

    def __getitem__(self, column_name):
        """
        Returns the correspondign column from the name when calling
        an element of this Class through []
        """
        if column_name not in self.columns.keys():
            raise Exception('Invalid column name: {}. \n'.format(column_name) +
                            'Options:\n' + '\n'.join(self.columns.keys())
                            )

        return self.data[:, self.columns[column_name]]
