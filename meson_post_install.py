#!/usr/bin/env python3

import os
import subprocess

schemadir = os.path.join("/", "usr", "share", "glib-2.0", "schemas")

if not os.environ.get("DESTDIR"):
    print("Compiling gsettings schemas...")
    subprocess.call(["glib-compile-schemas", schemadir])