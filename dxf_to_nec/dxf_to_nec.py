import ezdxf

SCALE_FACTOR = 0.001

def coordinate_float(val):
    val = val * SCALE_FACTOR

    if abs(val) < 0.001:
        val = 0

    s = "{:.5E}".format(val)

    if s[0] != "-":
        s = " " + s

    return s

def diameter_float(val):
    s = "{:>.5E}".format(val)

    if s[0] != "-":
        s = " " + s

    return s

def output(s):
    print(s)

def output_geometry(id, segments, start, end, diameter):

    output(f'GW {id:>5} {segments:>5}  {coordinate_float(start[0])} {coordinate_float(start[1])} {coordinate_float(start[2])} {coordinate_float(end[0])} {coordinate_float(end[1])} {coordinate_float(end[2])} {diameter_float(diameter)}')

def output_ge():
    output(f'GE     0     0   0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00')

def output_gn():
    output(f'GN     2     0     0      0  1.30000E+01  5.00000E-03  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00')

def process_dxf(filename):
    doc = ezdxf.readfile(filename)

    lines = doc.modelspace().query("LINE")
    OFFSET = (0, 0, 10 / SCALE_FACTOR)
    MIRROR_Y = True

    output(f'CM Model generated from {filename}')
    output(f'CE')

    idx = 1
    segments = 31   # TODO: Scale this based on length of the wire
    diameter = 0.002 # 2mm

    for line in lines:

        start = line.dxf.start
        end = line.dxf.end

        if MIRROR_Y:
            mirrored_start = (end[0], -end[1], end[2])
            mirrored_end = (start[0], -start[1], start[2])

            output_geometry(idx, segments, mirrored_start, mirrored_end, diameter )
            idx += 1

        output_geometry(idx, segments, start, end, diameter )
        idx += 1

    if OFFSET != (0, 0, 0):
        # Use a GM card to translate the existing geometry
        output(f'GM   0    0  0.00000E+00  0.00000E+00  0.00000E+00 {coordinate_float(OFFSET[0])} {coordinate_float(OFFSET[1])} {coordinate_float(OFFSET[2])}          0')


    output_ge()

    output_gn()

    output(
    '''EX     0     1     1      0  1.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00
FR     0    10     0      0  1.75000E+01  2.22222E-01  1.95000E+01  0.00000E+00  0.00000E+00  0.00000E+00
RP     0    90   361   1000  0.00000E+00  0.00000E+00  1.00000E+00  1.00000E+00  0.00000E+00  0.00000E+00
EN     0     0     0      0  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00''')


if __name__ == "__main__":
    filename = "Antenna Models - Bent Yagi Layout - 20m.dxf"
    # filename = "20m Rope Yagi - Dipole Layout.dxf"
    # filename = "20m Rope Yagi - Straight Yagi 20m.dxf"

    process_dxf(filename)