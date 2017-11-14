import argparse
import csv
import math
import sys

import yaml
import yaixm

MINIMUM_HEIGHT = 600

EXCLUDE_AREAS = [[51.3, 51.7, -0.25, 0.1],  # London
                 [53.5, 55.25, -10, -5.5],  # N Ireland
                 [53.4, 53.5, -2.3, -2.15]] # Manchester

def dms(latlon):
    assert len(latlon) == 10 or len(latlon) == 11

    s = round(float(latlon[-6:-1]))
    m = int(latlon[-8:-6])
    d = int(latlon[:-8])

    if s == 60:
        s = 0
        m += 1

    if m == 60:
        m = 0
        d += 1

    return {'h': latlon[-1].upper(), 'd': d, 'm': m, 's': s}

def parse_position(posn):
    lat, lon = posn.split()
    lat_dms = dms(lat)
    lon_dms = dms(lon)

    lat_str = "{0[d]:02d}{0[m]:02d}{0[s]:02d}{0[h]}".format(lat_dms)
    lon_str = "{0[d]:03d}{0[m]:02d}{0[s]:02d}{0[h]}".format(lon_dms)

    return lat_str + " " + lon_str

def inside_area(position, areas):
    lat, lon = position.split()
    lat = math.degrees(yaixm.radians(lat))
    lon = math.degrees(yaixm.radians(lon))

    for area in areas:
        if lat > area[0] and lat < area[1] and lon > area[2] and lon < area[3]:
            return True

    return False

def read_obstacles(csv_file):
    reader = csv.DictReader(csv_file)

    obstacles = []
    for obs in reader:
        id = [x for x in obs['Designation/Identification'].split()
              if x.startswith('UK')][0]

        # Ignore if height or elevation < MINIMUM_HIEGHT
        if obs['Height'] != "" and int(obs['Height'].split()[0]) < MINIMUM_HEIGHT:
            continue

        if obs['Elevation'] == "Unknown":
            continue

        elevation = obs['Elevation'].split()[0] + " ft"
        if int(elevation.split()[0]) < MINIMUM_HEIGHT:
            continue

        # Ignore offshore types
        typ = obs['Obstacle Type'].split()[0]
        if typ in ["OPH", "PFS", "PPL", "PPP", "TURB-OFF"]:
            continue

        # Ignore if inside exclude areas
        position = parse_position(obs['Obstacle Position'])
        if inside_area(position, EXCLUDE_AREAS):
            continue

        obstacles.append({'id': id,
                          'type': typ,
                          'elevation': elevation,
                          'position': position})

    return obstacles

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("obstacle_csv", help="ENR obstacle CSV data",
                        type=argparse.FileType("r"))
    parser.add_argument("yaml_file", nargs="?",
                        help="YAML output file, stdout if not specified",
                        type=argparse.FileType("w"), default=sys.stdout)

    args = parser.parse_args()

    obstacles = read_obstacles(args.obstacle_csv)

    # Write to YAML file
    yaml.add_representer(dict, yaixm.ordered_map_representer)
    yaml.dump({'obstacle': obstacles},
              args.yaml_file, default_flow_style=False)

