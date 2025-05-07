import struct
import numpy


def read_bcrf_file(filename):
    header_size = 4096
    data_size = 746 * 283 * 4  # Assuming 32-bit floating point data (bcrf format)

    with open(filename, 'rb') as file:
        # Read the header
        header = file.read(header_size)

        # Parse the header values
        header_dict = {}
        decoded_header = header.decode('utf-16le')
        for line in decoded_header.split('\n'):
            if '=' in line:
                key, value = line.strip().split('=')
                header_dict[key.strip()] = value.strip()

        # Read the data
        data = file.read(data_size)
    return header_dict, data


def write_bcrf_file(filename, data,  x_pixels, y_pixels, x_length, y_length, z_unit):
    header_size = 4096

    if type(x_length) == float:
        x_length = "{:.0f}".format(x_length)
    if type(y_length) == float:
        y_length = "{:.0f}".format(y_length)

    header_dict = {
        'fileformat': 'bcrf_unicode',
        'headersize': '2048',
        'xpixels': str(x_pixels),
        'ypixels': str(y_pixels),
        'xlength': x_length,
        'ylength': y_length,
        'scanspeed': '0',
        'intelmode': '1',
        'bit2nm': '1',
        'xoffset': '',
        'yoffset': '',
        'voidpixels': '',
        'zmin': '0',
        # 'xunit': '[mm]',
        # 'yunit': '[mm]',
        'zunit': z_unit,
        'forcecurve': '0'
    }

    # Create the header string
    header = ""
    for key, value in header_dict.items():
        header += key + " = " + str(value) + "\n"

    # Pad the header to the required size
    header = header.ljust(header_size//2, '%')

    with open(filename, 'wb') as file:
        # Write the header
        file.write(header.encode('utf-16le'))

        # Write the data
        data_bytes = struct.pack('<' + 'f' * len(data), *data)
        file.write(data_bytes)

    return header, data_bytes


def write_bcrf_file_with_header(filename, data, header_dict):
    header_size = 4096

    # Create the header string
    header = ""
    for key, value in header_dict.items():
        header += key + " = " + str(value) + "\n"

    # Pad the header to the required size
    header = header.ljust(header_size//2, '%')

    with open(filename, 'wb') as file:
        # Write the header
        file.write(header.encode('utf-16le'))

        # Write the data
        data_bytes = struct.pack('<' + 'f' * len(data), *data)
        file.write(data_bytes)
    return header, data_bytes


def convert_data_to_float(data):
    float_data = struct.unpack('<' + 'f' * (len(data) // 4), data)
    return float_data


def read_asc_file(filename):
    with open(filename, 'r') as file:
        header_dict = {}
        data_list = []
        file_data = file.readlines()
        for line in file_data:
            # Parse the header values
            if '=' in line and '#' in line:
                key, value = line.strip().split('=')
                header_dict[key.replace('#', '').strip()] = value.strip()
        for line in file_data:
            if '#' not in line:
                if line == '\n':
                    break
                line_list = line.split()
                data_list.append(line_list)
        data = numpy.array(data_list)
        return header_dict, data.astype('float')


def write_asc_file(filename, header_dict: dict, data):
    header = ""
    for key, value in header_dict.items():
        header += "# " + key + " = " + str(value) + "\n"

    data = numpy.rot90(data, k=1, axes=(1, 0))
    with open(filename, 'w') as file:
        file.write(header)
        file.write('\n# Start of Data:\n')
        for row in data:
            line = ' '.join([str(element) for element in row]) + '\n'
            file.write(line)


def data_binary_with_intensity(threshold, distance_file, intensity_file, new_filename):
    d_header, d_data = read_asc_file(distance_file)
    i_header, i_data = read_asc_file(intensity_file)
    # 使用閥值條件進行二維化
    binary_array = numpy.where(i_data >= threshold, 1, 0)
    new_d = d_data * binary_array
    write_asc_file(header_dict=d_header, filename=new_filename, data=new_d.T)


def z_correction_at_position_in_fb(coefs, poly_dim, _x, _y, _remove_linear_terms):
    # Initialize the result variable
    result = 0
    telecentric_correction_poly_dim = poly_dim

    if coefs:
        i = 0
        j = 1

        if _remove_linear_terms:
            # Remove linear terms from the calculation
            i = 2
            j = 2

        # Calculate the telecentric correction using the polynomial
        for dim in range(j, telecentric_correction_poly_dim + 1):
            # Add the contribution of each term to the result
            result += _x ** dim * coefs[i]
            i += 1
            result += _y ** dim * coefs[i]
            i += 1

            if dim > 1:
                # Add the cross-term contributions
                for k in range(1, dim):
                    result += _x ** k * _y ** (dim - k) * coefs[i]
                    i += 1
    else:
        # If there are no coefficients, the result is zero
        result = 0

    return result


def fss_calibration_data(sensor, coefs, unit_x, unit_y, x_pixel, y_pixel, file_name):
    if sensor == 'FSS80':
        z_coff_factor = 366
        poly_dim = 4
    else:
        z_coff_factor = 199
        poly_dim = 8

    # Define the range unit for generating x and y values
    range_unit_x = unit_x
    range_unit_y = unit_y

    # Generate an array of x values
    x_values = numpy.linspace(-range_unit_x, range_unit_x, x_pixel)

    # Generate an array of y values
    y_values = numpy.linspace(-range_unit_y, range_unit_y, y_pixel)

    # Create a 2D array to store the results
    results = numpy.zeros((len(y_values), len(x_values)))

    # Calculate the Z correction for each combination of x and y values
    for i, y_value in enumerate(y_values):
        for j, x_value in enumerate(x_values):
            remove_linear_terms = True  # Replace with the specific value you want
            result = z_correction_at_position_in_fb(coefs, poly_dim, x_value, y_value, remove_linear_terms)
            results[i, j] = result

    # 將結果保存為ASC格式的純文本文件
    with open(file_name, 'w') as file:
        # 寫入header
        file.write("# File Format = ASCII\n")
        file.write("# Created Monday, 29. May 2023\n")
        file.write("# x-pixels = {}\n".format(len(x_values)))
        file.write("# y-pixels = {}\n".format(len(y_values)))
        file.write("# x-length = {}\n".format(int(range_unit_x / z_coff_factor * 2 * 1000000)))
        file.write("# y-length = {}\n".format(int(range_unit_y / z_coff_factor * 2 * 1000000)))
        file.write("# x-offset = 1\n")
        file.write("# y-offset = 0\n")
        file.write("# z-unit = um\n")
        file.write("# voidpixels = \n")
        file.write("# description =0:\n")
        file.write("# Start of Data:\n")

        # 寫入主要內容
        for i in range(len(y_values)):
            for j in range(len(x_values)):
                file.write("{:.6f} ".format(results[i, j]))


if __name__ == "__main__":
    pass
    # region Example usage - BCRF - read file & write
    # header, binary_data = read_bcrf_file('test.bcrf')
    # data = convert_data_to_float(binary_data)
    # h1, d1 = write_bcrf_file(filename='new.bcrf', data=data, x_pixels=header['xpixels'], y_pixels=header['ypixels'],
    #                          x_length=header['xlength'], y_length=header['ylength'], z_unit='um')
    # h2, d2 = write_bcrf_file_with_header(filename='new.bcrf', data=data, header_dict=header)
    # endregion

    # region Example usage - BCRF - create data and write file
    # data = numpy.random.rand(3, 3)
    # data_flat = data.flatten()
    # write_bcrf_file(filename='new.bcrf', data=data_flat, x_pixels='3', y_pixels='3',
    #                 x_length='30', y_length='30', z_unit='um')
    # endregion

    # region Example usage - ASC
    # header = {
    #     "File Format": 'ASCII',
    #     "Original file": '',
    #     "x-pixels": '67',
    #     "y-pixels": '12',
    #     "x-length": '660000',
    #     "y-length": '276736.843',
    #     "x-offset": '-4609999.1',
    #     " y-offset": '-1823947.5',
    #     "z - unit": 'nm',
    #     "scanspeed": '1.32000002e-12',
    #     "forcecurve": '0',
    #     "voidpixels": '337',
    #     "description": '142:Calculated from expression:'
    # }
    # write_asc_file(header_dict=header, filename='new.asc')
    # endregion

    # region Example usage - 使用閥值條件進行二維化
    # distance_file = 'C:\\Users\\alex.lin\Desktop\\testfile\\Altitude_40%_CLS02.asc'
    # intensity_file = 'C:\\Users\\alex.lin\Desktop\\testfile\\Intensity_40%_CLS02.asc'
    # new_filename = 'C:\\Users\\alex.lin\Desktop\\testfile\\Binary_Distance.asc'
    # data_binary_with_intensity(threshold=0.2, distance_file=distance_file, intensity_file=intensity_file,
    #                            new_filename=new_filename)
    # x_pixels = 900
    # y_pixels = 200
    # x_length = 16226
    # y_length = 16691
    # endregion

    # region Example usage - Create FSS Calibration data
    x_pixels = 800
    y_pixels = 800
    # unit: mm
    x_length = 320
    y_length = 320
    u_x = x_length / 2 * 199
    u_y = y_length / 2 * 199
    m_telecentric_correction_coefs_current_80 = [
           0.00350810047896506, 0.00720094018752011, 1.5885558396392E-7,
           -7.70171143325849E-7, 3.49155649272977E-9, -6.38436658317153E-14,
           -9.95277668553992E-13, 4.46603623552055E-14, -1.1814754437931E-12,
           1.23412312116527E-15, 1.16595107678301E-15, -1.30740998289136E-17,
           2.47079643928364E-15, -1.15579004661399E-17, 989.603626497689
        ]

    m_telecentric_correction_coefs_current_310 = [
        -2.87437560473336E-5, 0.000108478590846062, -4.95839969971712E-7, 5.84202155096136E-7, 8.28134361086086E-9,
        4.29523848129512E-13, 1.88893049964632E-13, 1.34589867666047E-14, 1.86309016716839E-13, -1.79608929246971E-16,
        -2.82148818782555E-16, -1.05963118597992E-17, -4.57431725774772E-16, -1.18039384786644E-17,
        -2.09312985101911E-21, -4.70718161528554E-23, 5.61870849800225E-23, 5.58277935475741E-23, -1.68823630077144E-22,
        1.74974476373904E-23, -7.70299932567535E-26, 3.09290698077144E-26, 7.03764538037437E-27, -1.57045418283364E-25,
        1.18808692339304E-26, -1.88782401836053E-25, 9.47791263496571E-27, 1.040741508896E-30, -1.81153156884918E-32,
        -4.14995115021079E-32, -1.12268174062854E-31, -1.10063687222153E-31, -5.06787000338655E-32,
        -5.94665194764603E-31, 3.38015134433116E-32, 1.50852487217407E-35, -3.1209231521369E-35, -4.87391605223854E-36,
        1.56167825289958E-35, -9.35773141848865E-36, 8.9310915409734E-35, -1.31041633541132E-35, 4.32399053670877E-35,
        -5.48970103510561E-36, 1117.30871582031
    ]
    filename = "C:\\Users\\alex.lin\\Desktop\\corr.asc"
    fss_calibration_data('FSS310', m_telecentric_correction_coefs_current_310, u_x, u_y, x_pixels, y_pixels,
                         filename)
    # endregion




