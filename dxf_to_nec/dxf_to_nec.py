import argparse
import ezdxf
import sys
import math
from pathlib import Path
import os

def coordinate_float(val):
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

def output(s, output_file):
    if output_file:
        output_file.write(s + "\n")
    else:
        print(s)

def wire_length(start, end):
    x = abs(start[0] - end[0])
    y = abs(start[1] - end[1])

    return math.sqrt(pow(x, 2) + pow(y, 2))

def output_geometry(id, segments_per_meter, start, end, diameter, output_file):
    segments = round(wire_length(start, end) * segments_per_meter)

    output(f'GW {id:>5} {segments:>5}  {coordinate_float(start[0])} {coordinate_float(start[1])} {coordinate_float(start[2])} {coordinate_float(end[0])} {coordinate_float(end[1])} {coordinate_float(end[2])} {diameter_float(diameter)}', output_file)

def output_ge(output_file):
    output(f'GE     1     0   0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00', output_file)

def output_gn(output_file):
    output(f'GN     2     0     0      0  1.30000E+01  5.00000E-03  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00', output_file)

def output_exeuction(frequency, output_file=None):
    iterations = 30
    start_frequency = frequency - (frequency * 0.1)
    end_frequency = frequency + (frequency * 0.1)
    excitation_tag = 1
    excitation_segment = 1

    frequency_step = (end_frequency - start_frequency) / iterations

    output(
    f'''EX     0 {excitation_tag:>5} {excitation_segment:>5}      0  1.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00
FR     0   {iterations:>3}     0      0  {coordinate_float(start_frequency)}  {coordinate_float(frequency_step)} {coordinate_float(end_frequency)}  0.00000E+00  0.00000E+00  0.00000E+00
RP     0    90   361   1000  0.00000E+00  0.00000E+00  1.00000E+00  1.00000E+00  0.00000E+00  0.00000E+00
EN     0     0     0      0  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00''', output_file)



def process_dxf(filename, scale, output_filename, frequency, segments_per_meter, diameter, offset, mirror_y):

    doc = ezdxf.readfile(filename)

    output_file = None
    if output_filename:
        output_file = open(output_filename, 'w')

    lines = doc.modelspace().query("LINE")

    ## Comment Card Section
    output(f'CM Model generated from {filename}', output_file)
    output(f'CE', output_file)

    # Begin Geometry

    idx = 1

    for line in lines:

        start = line.dxf.start * scale
        end = line.dxf.end * scale

        output_geometry(idx, segments_per_meter, start, end, diameter, output_file)
        idx += 1

        # Mirror cards around the Y axis
        if mirror_y:
            mirrored_start = (end[0], -end[1], end[2])
            mirrored_end = (start[0], -start[1], start[2])

            output_geometry(idx, segments_per_meter, mirrored_start, mirrored_end, diameter, output_file)
            idx += 1

    if offset != (0, 0, 0):
        # Use a GM card to translate the existing geometry
        output(f'GM   0    0  0.00000E+00  0.00000E+00  0.00000E+00 {coordinate_float(offset[0])} {coordinate_float(offset[1])} {coordinate_float(offset[2])}          1', output_file)


    # Geometry End
    output_ge(output_file)

    # Ground setup
    output_gn(output_file)

    # EX, RF, RP and EN cards
    output_exeuction(frequency, output_file)

    if output_file:
        output_file.close()


def parse_xyz(value):
    try:
        x, y, z = map(float, value.split(','))
        return (x, y, z)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid XYZ format: '{value}'. Expected 'x,y,z'")

def main():
    parser = argparse.ArgumentParser(
        description='Convert DXF files to NEC (Numerical Electromagnetics Code format'
    )
    parser.add_argument('filenames', nargs='+', help='Input DXF file path(s) or directory')
    parser.add_argument('-o', '--output', help='Output file path (default: stdout)')
    parser.add_argument('-f', '--frequency', type=float, default=14.1, help='Target frequency for the antenna in MHz (default: 14.1)')
    parser.add_argument('-s', '--segments', type=float, default=20, help='Segments per wavelength (default: 20)')
    parser.add_argument('-d', '--diameter', type=float, default=0.002, help='Wire diameter in meters (default: 0.002)')
    parser.add_argument('-S', '--scale', type=float, default=0.001, help='Scale factor for the DXF to meters (default: 0.001)')
    parser.add_argument('-O', '--offset', type=parse_xyz, default=(0, 0, 5),
                        help='Geometry offset as comma-separated XYZ in meters (default: 0,0,5)')
    parser.add_argument('--no-mirror', action='store_true', help='Disable Y-axis mirroring')

    args = parser.parse_args()

    output_file = None
    if args.output:
        output_file = open(args.output, 'w')

    expanded_files = []
    for filename in args.filenames:
        path = Path(os.path.expanduser(filename))
        if path.is_dir():
            expanded_files.extend(sorted(path.glob("*.dxf")))
        elif path.exists():
            expanded_files.append(path)
        else:
            parser.error(f"Input file or directory not found: {filename}")

    if not expanded_files:
        parser.error("No DXF files found to process")

    output_filename = args.output
    output_dir = None
    if output_filename:
        output_path = Path(os.path.expanduser(output_filename))
        if output_path.is_dir():
            output_dir = output_path
            output_filename = None

    if len(expanded_files) > 1 and not output_filename:
        if output_dir:
            output_filename = str(output_dir / (str(expanded_files[0].stem) + '.nec'))
        else:
            output_filename = str(expanded_files[0].with_suffix('.nec'))

    wavelength = 300 / args.frequency
    segments_per_meter = args.segments / wavelength

    for file_path in expanded_files:
        if output_dir:
            file_output_filename = str(output_dir / (str(file_path.stem) + '.nec'))
        elif len(expanded_files) > 1:
            file_output_filename = str(file_path.with_suffix('.nec'))
        else:
            file_output_filename = output_filename

        process_dxf(
            filename=str(file_path),
            scale=args.scale,
            output_filename=file_output_filename,
            frequency=args.frequency,
            segments_per_meter=segments_per_meter,
            diameter=args.diameter,
            offset=args.offset,
            mirror_y=not args.no_mirror
        )

if __name__ == "__main__":
    main()