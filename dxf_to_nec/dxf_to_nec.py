import argparse
import ezdxf
import sys

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

def output(s, output_file=None):
    if output_file:
        output_file.write(s + "\n")
    else:
        print(s)

def output_geometry(id, segments, start, end, diameter, output_file=None):

    output(f'GW {id:>5} {segments:>5}  {coordinate_float(start[0])} {coordinate_float(start[1])} {coordinate_float(start[2])} {coordinate_float(end[0])} {coordinate_float(end[1])} {coordinate_float(end[2])} {diameter_float(diameter)}', output_file)

def output_ge(output_file=None):
    output(f'GE     0     0   0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00', output_file)

def output_gn(output_file=None):
    output(f'GN     2     0     0      0  1.30000E+01  5.00000E-03  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00', output_file)

def process_dxf(filename, output_file=None, segments=31, diameter=0.002, offset=(0, 0, 10 / SCALE_FACTOR), mirror_y=True):

    doc = ezdxf.readfile(filename)

    lines = doc.modelspace().query("LINE")

    output(f'CM Model generated from {filename}', output_file)
    output(f'CE', output_file)

    idx = 1

    for line in lines:

        start = line.dxf.start
        end = line.dxf.end

        if mirror_y:
            mirrored_start = (end[0], -end[1], end[2])
            mirrored_end = (start[0], -start[1], start[2])

            output_geometry(idx, segments, mirrored_start, mirrored_end, diameter, output_file)
            idx += 1

        output_geometry(idx, segments, start, end, diameter, output_file)
        idx += 1

    if offset != (0, 0, 0):
        # Use a GM card to translate the existing geometry
        output(f'GM   0    0  0.00000E+00  0.00000E+00  0.00000E+00 {coordinate_float(offset[0])} {coordinate_float(offset[1])} {coordinate_float(offset[2])}          0', output_file)


    output_ge(output_file)

    output_gn(output_file)

    output(
    '''EX     0     1     1      0  1.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00
FR     0    10     0      0  1.75000E+01  2.22222E-01  1.95000E+01  0.00000E+00  0.00000E+00  0.00000E+00
RP     0    90   361   1000  0.00000E+00  0.00000E+00  1.00000E+00  1.00000E+00  0.00000E+00  0.00000E+00
EN     0     0     0      0  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00''', output_file)


def parse_xyz(value):
    try:
        x, y, z = map(float, value.split(','))
        return (x / SCALE_FACTOR, y / SCALE_FACTOR, z / SCALE_FACTOR)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid XYZ format: '{value}'. Expected 'x,y,z'")

def main():
    parser = argparse.ArgumentParser(
        description='Convert DXF files to NEC (Numerical Electromagnetics Code) format'
    )
    parser.add_argument('filename', help='Input DXF file path')
    parser.add_argument('-o', '--output', help='Output file path (default: stdout)')
    parser.add_argument('-s', '--segments', type=int, default=31, help='Number of segments per wire (default: 31)')
    parser.add_argument('-d', '--diameter', type=float, default=0.002, help='Wire diameter in meters (default: 0.002)')
    parser.add_argument('-O', '--offset', type=parse_xyz, default=(0, 0, 10 / SCALE_FACTOR),
                        help='Geometry offset as comma-separated XYZ in meters (default: 0,0,10)')
    parser.add_argument('--no-mirror', action='store_true', help='Disable Y-axis mirroring')

    args = parser.parse_args()

    output_file = None
    if args.output:
        output_file = open(args.output, 'w')

    try:
        process_dxf(
            filename=args.filename,
            output_file=output_file,
            segments=args.segments,
            diameter=args.diameter,
            offset=args.offset,
            mirror_y=not args.no_mirror
        )
    finally:
        if output_file:
            output_file.close()

if __name__ == "__main__":
    main()