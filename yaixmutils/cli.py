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
import json
import os.path
import subprocess
import sys
import tempfile

from pyparsing import ParseException
import yaixm
import yaml

from .tnp import Tnp, normalise
from .obstacle import read_obstacles

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

def convert_obstacles():
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

