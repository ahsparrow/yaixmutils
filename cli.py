import sys

import yaixmutils.cli as cli

script_name = sys.argv[1]
sys.argv.pop(1)

if script_name == "obstacle":
    cli.convert_obstacle()
elif script_name == "release":
    cli.release()
elif script_name == "ils":
    cli.calc_ils()
elif script_name == "point":
    cli.calc_point()
elif script_name == "stub":
    cli.calc_stub()
elif script_name == "check_service":
    cli.check_service()
else:
    print("Unrecognised script: " + script_name, file=sys.stderr)

