import sys

import yaixmutils.cli as cli

script_name = sys.argv[1]
sys.argv.pop(1)

if script_name == "tnp":
    cli.convert_tnp()
elif script_name == "obstacle":
    cli.convert_obstacle()
elif script_name == "release":
    cli.release()
else:
    print("Unrecognised script: " + script_name, file=sys.stderr)

