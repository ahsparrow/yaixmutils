import sys

import yaixmutils.cli as cli

script_name = sys.argv[1]
sys.argv.pop(1)

if script_name == "tnp":
    cli.convert_tnp()
else:
    print("Unrecognised script: " + script_name, file=sys.stderr)

