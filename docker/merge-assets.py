"""Merge an app's asset manifest into the image's baked manifest.

`bench build --app <app>` rewrites sites/assets/assets.json with ONLY the app it
just built. For hrms that file is ~400 bytes, against ~3.7KB in the base image
which maps every frappe and erpnext bundle. Copying it wholesale into the
runtime image would therefore drop all of those mappings and break the entire
desk, not just HR.

So: merge, never replace. Run at image build time.

Usage:
    merge-assets.py <assets-dir> <extra-assets.json> [<extra-assets-rtl.json>]
"""

import json
import os
import sys


def merge(target_path, extra_path):
    if not os.path.exists(extra_path):
        print("skip (no such file): %s" % extra_path)
        return
    if not os.path.exists(target_path):
        print("skip (no baked manifest): %s" % target_path)
        return

    with open(target_path) as fh:
        merged = json.load(fh)
    before = len(merged)

    with open(extra_path) as fh:
        extra = json.load(fh)

    merged.update(extra)

    # Refuse to write a manifest smaller than what we started with — that would
    # mean we replaced rather than merged, which is the exact bug this exists
    # to prevent.
    if len(merged) < before:
        raise SystemExit(
            "refusing to shrink %s: %d -> %d entries" % (target_path, before, len(merged))
        )

    with open(target_path, "w") as fh:
        json.dump(merged, fh)

    print("%s: %d -> %d entries (+%d from %s)" % (
        os.path.basename(target_path), before, len(merged),
        len(merged) - before, os.path.basename(extra_path)))


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)

    assets_dir = sys.argv[1]
    merge(os.path.join(assets_dir, "assets.json"), sys.argv[2])
    if len(sys.argv) > 3:
        merge(os.path.join(assets_dir, "assets-rtl.json"), sys.argv[3])


if __name__ == "__main__":
    main()
