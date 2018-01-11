# Copyright 2017 Alan Sparrow
#
# This file is part of YAIXM utils
#
# YAIXM utils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YAIXM utils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YAIXM utils.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import datetime
import json
import os.path
import re
import subprocess
import sys
import tempfile

from pygeodesy.ellipsoidalVincenty import LatLon
from pyparsing import ParseException
import yaixm
import yaml

from .tnp import Tnp, normalise
from .obstacle import read_obstacles

# Convert TNP airspace data to nominal YAIXM format
def convert_tnp():
    parser = argparse.ArgumentParser()
    parser.add_argument("tnp_file", nargs="?",
                        help="TNP airspace file",
                        type=argparse.FileType("r"), default=sys.stdin)
    parser.add_argument("yaixm_file", nargs="?",
                        help="YAIXM output file, stdout if not specified",
                        type=argparse.FileType("w"), default=sys.stdout)
    args = parser.parse_args()

    tnp_parser = Tnp.parser()
    try:
        results = tnp_parser.parseFile(args.tnp_file)
    except ParseException as e:
        print("No match {0}".format(str(e)))

    airspace = normalise(results)

    # Write to YAML file
    yaml.add_representer(dict, yaixm.ordered_map_representer)
    yaml.dump({'airspace': airspace},
               args.yaixm_file, default_flow_style=False)

# Convert obstacle data XLS spreadsheet from AIS to YAXIM format
def convert_obstacle():
    parser = argparse.ArgumentParser()
    parser.add_argument("obstacle_xls", help="ENR obstacle XLS data")
    parser.add_argument("yaml_file", nargs="?",
                        help="YAML output file, stdout if not specified",
                        type=argparse.FileType("w"), default=sys.stdout)

    args = parser.parse_args()

    # Using temporary working directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Convert xls to xlsx
        subprocess.run(["libreoffice",
             "--convert-to", "xlsx",
             "--outdir", tmp_dir,
             args.obstacle_xls], errors=True)

        base_xls = os.path.basename(args.obstacle_xls)
        base_xlsx = os.path.splitext(base_xls)[0] + ".xlsx"
        xlsx_name = os.path.join(tmp_dir, base_xlsx)

        # Convert xlsx to CSV
        csv_name = os.path.join(tmp_dir, "obstacle.csv")
        subprocess.run(["xlsx2csv",
                        "--sheetname" , "All", xlsx_name, csv_name],
                       errors=True)

        obstacles = read_obstacles(open(csv_name))

    # Write to YAML file
    yaml.add_representer(dict, yaixm.ordered_map_representer)
    yaml.dump({'obstacle': obstacles},
              args.yaml_file, default_flow_style=False)

# Get next AIRAC effective date after today
def get_airac_date(prev=False):
    # AIRAC cycle is fixed four week schedule
    airac_date = datetime.date(2017, 11, 9)
    today = datetime.date.today()
    while airac_date < today:
        airac_date += datetime.timedelta(days=28)

    if prev:
        airac_date -= datetime.timedelta(days=28)

    return airac_date.isoformat() + "T00:00:00Z"

# Convert collection of YAIXM files containing airspace, LOAs and
# obstacles to single JSON file with release header
def release():
    parser = argparse.ArgumentParser()
    parser.add_argument("yaixm_file", nargs="+",
                        type=argparse.FileType("r"),
                        help="Airspace, LOA or obstacle file")
    parser.add_argument("release_file", help="JSON output file")
    parser.add_argument("--indent", "-i", type=int, default=None,
                        help="JSON file indentation level (default none)")
    parser.add_argument("--force", "-f", action="store_true", default=False,
                        help="Force overwrite of existing release file")
    parser.add_argument("--prev", "-p", action="store_true", default=False,
                        help="Use previous AIRAC date")
    parser.add_argument("--note", "-n", help="Release note file",
                        type=argparse.FileType("r"), default=None)

    args = parser.parse_args()

    if args.release_file == "-":
        release_file = sys.stdout
    else:
        try:
            if args.force:
                release_file = open(args.release_file, "w")
            else:
                try:
                    release_file = open(args.release_file, "x")
                except FileExistsError:
                    print("ERROR: Can't overwrite existing release file")
                    sys.exit(-1)
        except PermissionError:
            print("ERROR: Release file permission denied")
            sys.exit(-1)

    # Aggregate input files
    out = {}
    for f in args.yaixm_file:
        out.update(yaixm.load(f))

    # Append release header
    header = {
        'schema_version': 1,
        'airac_date': get_airac_date(args.prev_airac),
        'timestamp': datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    }
    if args.note:
        header['note'] = args.note.read()
    out.update({'release': header})

    # Validate final output
    error = yaixm.validate(out)
    if error:
        print(error)
        sys.exit(-1)

    json.dump(out, release_file, sort_keys=True, indent=args.indent)

def calc_ils():
    parser = argparse.ArgumentParser()
    parser.add_argument("lat", help="Centre latitude, DMS e.g. 512345N")
    parser.add_argument("lon", help="Centre longitude, DMS e.g. 0012345W")
    parser.add_argument("bearing", type=float, help="Runway bearing, degrees")
    parser.add_argument("radius", type=float, nargs="?", default=2,
                        help="ATZ radius, in nm (default 2)")
    args = parser.parse_args()

    lon = yaixm.parse_deg(args.lon)
    lat = yaixm.parse_deg(args.lat)
    centre = LatLon(lat, lon)

    bearing = args.bearing + 180
    radius = args.radius * 1852

    distances = [radius, 8 * 1852, 8 * 1852, radius]
    bearings = [bearing -3, bearing -3, bearing + 3, bearing + 3]

    for d, b in zip(distances, bearings):
        p = centre.destination(d, b)
        print("- %s" % p.toStr(form="sec", prec=0, sep=" "))
