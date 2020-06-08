#!/usr/bin/env python
import sys
import yaml

if len(sys.argv) < 2:
    print("No version was provided!")
    sys.exit(1)

version = sys.argv[1]
with open("galaxy.yml.in") as f:
    y = yaml.safe_load(f)
y['version'] = version
with open("galaxy.yml", "w") as ff:
    yaml.safe_dump(y, ff)
