# Copyright 2017 Alan Sparrow
#
# This file is part of Airplot
#
# Airplot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Airplot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Airplot.  If not, see <http://www.gnu.org/licenses/>.

import pyparsing as pp

class Tnp:
  # "="s are parsed but discarded
  eq = pp.Suppress(pp.Word("="))

  # Heights, levels, etc.
  flight_level = pp.Group("FL" + pp.Word(pp.nums, min=2, max=3))
  altitude = pp.Group(pp.Word(pp.nums, min=3) + "ALT")
  height = pp.Group(pp.Word(pp.nums) + "AGL")
  surface = pp.Group("SFC")

  # Swap ordering of fields for height and altitude for consistance with FL
  altitude = altitude.setParseAction(lambda t: [[t[0][1], t[0][0]]])
  height = height.setParseAction(lambda t: [[t[0][1], t[0][0]]])

  level = (flight_level ^ altitude ^ height ^ surface).setResultsName('level')

  base = pp.Group(pp.Literal("BASE").suppress() +
                  eq + level).setResultsName('base')
  tops = pp.Group(pp.Literal("TOPS").suppress() +
                  eq + level).setResultsName('tops')

  # Airspace type
  airways = pp.oneOf("AIRWAYS A").setParseAction(lambda: "AIRWAYS")
  cta = pp.oneOf("CTA/CTR C").setParseAction(lambda: "CTA/CTR")
  danger = pp.oneOf("DANGER D").setParseAction(lambda: "DANGER")
  gsec = pp.oneOf("GSEC G").setParseAction(lambda: "GSEC")
  matz = pp.oneOf("MATZ M").setParseAction(lambda: "MATZ")
  other = pp.oneOf("OTHER 0").setParseAction(lambda: "OTHER")
  prohibited = pp.oneOf("PROHIBITED P").setParseAction(lambda: "PROHIBITED")
  restricted = pp.oneOf("RESTRICTED R").setParseAction(lambda: "RESTRICTED")
  tmz = pp.oneOf("TMZ T").setParseAction(lambda: "TMZ")

  # Airspace type extensions for ukair generated TNP
  rmz = pp.Literal("RMZ").setParseAction(lambda: "RMZ")

  as_val = (airways ^ cta ^ danger ^ gsec ^ matz ^ other ^ prohibited ^
            restricted ^ tmz ^ rmz).setResultsName('val')
  as_type = pp.Group(
      pp.Literal("TYPE").suppress() + eq + as_val).setResultsName('type')

  # Airspace class
  class_val= pp.Optional(pp.oneOf("A B C D E F G X").setResultsName('val'))
  as_class = pp.Group(
      pp.Literal("CLASS").suppress() + eq + class_val).setResultsName('class')

  # Airspace title (can contain *single* spaces)
  title_val = pp.Combine(pp.OneOrMore(
      pp.Word(pp.printables) | pp.White(" ", max=1) + ~pp.White()))
  title_val = title_val.setResultsName('title')
  title = pp.Literal("TITLE").suppress() + eq + title_val

  # Airspace coordinates
  lat = pp.Group(
      pp.Word("NS") + pp.Word(pp.nums, exact=6)).setResultsName('lat')
  lon = pp.Group(
      pp.Word("EW") + pp.Word(pp.nums, exact=7)).setResultsName('lon')

  radius_val = pp.Combine(
      pp.OneOrMore(pp.Word(pp.nums) + pp.Optional("." + pp.Word(pp.nums))))
  radius_val = radius_val.setResultsName('radius')
  radius = pp.Literal("RADIUS").suppress() + eq + radius_val

  centre = pp.Group(pp.Literal("CENTRE").suppress() +
                    eq + lat + lon).setResultsName('centre')

  to = pp.Group(pp.Literal("TO").suppress() +
                eq + lat + lon).setResultsName('to')

  point = pp.Group(pp.Literal("POINT").suppress() +
                   eq + lat + lon).setResultsName('point')
  circle = pp.Group(pp.Literal("CIRCLE").suppress() +
                    radius + centre).setResultsName('circle')
  cw_arc = pp.Group(pp.Literal("CLOCKWISE").suppress() +
                    radius + centre + to).setResultsName('cwarc')
  ccw_arc = pp.Group(pp.Literal("ANTI-CLOCKWISE").suppress() +
                     radius + centre + to).setResultsName('ccwarc')

  # Header must have BASE and TOPS plus optional TYPE and CLASS
  header = pp.Group(base & tops & pp.Optional(as_type) & pp.Optional(as_class))
  header = header.setResultsName('header')

  # Body is either CIRCLE, or POINT plus one or more POINTs/ARCs
  body = pp.Group(circle ^ (point + pp.OneOrMore(point ^ cw_arc ^ ccw_arc)))
  body = body.setResultsName('body')

  airspace = pp.Group(title + header + body).setResultsName('airspace')

  # Discard INCLUDEs and END
  include_yes = pp.Suppress(pp.Group("INCLUDE" + eq + "YES"))
  include_no = pp.Suppress(pp.Group("INCLUDE" + eq + "NO"))
  end = pp.Suppress(pp.Literal("END"))

  @classmethod
  def parser(cls):
    # Ingore comments including FILTERTAGs (for now)
    tnp = pp.OneOrMore(cls.airspace ^ cls.include_yes ^ cls.include_no ^
                       cls.as_class ^ cls.as_type) + cls.end
    tnp.ignore(pp.pythonStyleComment)
    return tnp

# Convert parsed TNP level to string
def level_str(level):
  if level[0] == 'SFC':
    str = "SFC"
  else:
    if level[0] == 'FL':
      str = "FL" + level[1]
    else:
      str = level[1] + " ft"
  return str

# Convert parsed TNP lat/long to string
def latlon_str(latlon):
  str = latlon['lat'][1] + latlon['lat'][0] + " " + \
        latlon['lon'][1] + latlon['lon'][0]
  return str

# Convert TNP parse result to standard python structures
def normalise(tnp):
  airspace_list = []
  as_class = 'X'
  as_type = None

  for block in tnp:
    # Class and type carry over to following blocks
    if block.getName() == 'class':
      as_class = block['val']
    elif block.getName() == 'type':
      as_type = block['val']
    elif block.getName() == 'airspace':

      boundary = []
      line = []
      for b in block['body']:
        if b.getName() == 'point':
          line.append(latlon_str(b))
        else:
          if line:
            boundary.append({'line': line})
            line = []

        if b.getName() == 'circle':
          boundary.append({
            'circle': {
              'radius': "%g nm" % (float(b['radius'])),
              'centre': latlon_str(b['centre'])
             }})

        if b.getName() in ['cwarc', 'ccwarc']:
          boundary.append({
            'arc': {
              'radius': "%g nm" % (float(b['radius'])),
              'centre': latlon_str(b['centre']),
              'to': latlon_str(b['to']),
              'dir': 'cw' if b.getName() == 'cwarc' else 'ccw'
            }})

      if line:
        boundary.append({'line': line})

      if 'class' in block['header']:
          as_class = block['header']['class'].get('val', "X")

      if 'type' in block['header']:
          as_type = block['header']['type']['val']

      airspace = {
        'name': block['title'],
        'type': as_type,
        'geometry': [{
          'lower': level_str(block['header']['base']['level']),
          'upper': level_str(block['header']['tops']['level']),
          'boundary': boundary
        }]
      }
      if as_class != "X":
          airspace['class'] = as_class

      airspace_list.append(airspace)

  return airspace_list

# Find and remove duplicate start/end points
def remove_duplicate_point(tnp):
    # First make (feature, volume) list of duplicates
    arr = []
    for as_idx, a in enumerate(tnp):
        for vol_idx, v in enumerate(a['geometry']):
            bdry = v['boundary']
            if 'line' in bdry[0] and 'line' in bdry[-1]:
                if bdry[0]['line'][0] == bdry[-1]['line'][-1]:
                    arr.append((as_idx, vol_idx))

    # ..then delete the duplicates
    for as_idx, vol_idx in arr:
        bdry = tnp[as_idx]['geometry'][vol_idx]['boundary']
        # Delete final point in final line
        del bdry[-1]['line'][-1]

        # If final line now has no points delete the line as well
        if not bdry[-1]['line']:
            del bdry[-1]

if __name__ == '__main__':
  from pprint import pprint
  import sys

  parser = Tnp.parser()
  try:
    results = parser.parseFile(sys.argv[1])
    airspace = normalise(results)
    pprint(airspace)
  except pp.ParseException as e:
    print("No match {0}".format(str(e)))
