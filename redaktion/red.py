import argparse
import os
import shutil
import sys
from os import path
from os.path import basename

from post import read_post_file, read_devices
from sidecar_tool import read_sidecar, add_sidecar_data
from tcxparser import TCXParser
from utility import debug, set_log_switch, out, error, init_out, build_post_path, post_file_name, z_date_to_locale_dt

args = None
tcx_suffixes = (".tcx", ".TCX")
post_file_archetype_path = "../archetypes/post.md"


def parse_args():
    global args

    parser = argparse.ArgumentParser(description='Bring your content into the Hugo blog')

    parser.add_argument("-v", "--verbose",
                        action='store_true',
                        help="Print more info")

    sub_parsers = parser.add_subparsers()

    # ######### load #########
    load_parser = sub_parsers.add_parser('load',
                                         help="Add activity files",
                                         description=""
                                         )

    load_parser.add_argument('dir', metavar='DIR', type=str,
                             help="Root directory to search for activity files or a particular file")

    load_parser.add_argument("-s", "--sidecar",
                             required=False,
                             help="Read additional data from side car file (csv). ")

    load_parser.add_argument("-d", "--delete",
                             action='store_true',
                             help="Delete the activity source file instead of copying it")

    load_parser.add_argument("-f", "--force",
                             action='store_true',
                             help="Overwrite instead of skipping existing posts")

    load_parser.set_defaults(func=execute_load)

    init_out()

    args = parser.parse_args()

    if args.verbose:
        set_log_switch(True)

    if len(sys.argv) > 1:
        args.func()
    else:
        out("Don't know what to do!")


def do_load(source_dir, force, delete, sidecar):
    out(f"loading from {source_dir}...")
    debug(f"load: {force}")

    if not path.exists(source_dir):
        error(f"Invalid source '{source_dir}'")

    if path.isdir(source_dir):
        files = list_files(source_dir)
    else:
        files = [source_dir]

    if len(files) == 0:
        exit("No files found")

    skipped = 0
    created = 0

    posts = []

    files = [f for f in files if f.endswith(tcx_suffixes)]
    cnt = 0
    for f in files:
        cnt += 1
        out(f"Processing {cnt}/{len(files)}: {basename(f)}")

        post = copy_tcx(f, force, delete)
        if post:
            posts.append(post)
            created += 1
        else:
            skipped += 1

    out_tcx = f"{created} posts created, {skipped} skipped."
    out(out_tcx)

    sidecar_added = 0
    sidecar_failed = 0
    if sidecar is not None:
        devices = read_devices()
        debug(f"devices={devices}")

        debug("Processing sidecar")
        data = read_sidecar(sidecar)
        # debug(f"Sidecar={data}")
        for p in posts:
            if add_sidecar_data(p, data, devices):
                sidecar_added += 1
            else:
                sidecar_failed += 1

        if sidecar_added == created:
            out_sidecar = f"All {sidecar_added} posts updated with Sidecar data, {sidecar_failed} failed."
        else:
            out_sidecar = f"Only {sidecar_added}/{created} posts updated with Sidecar data, {sidecar_failed} failed."

    if out_sidecar is not None:
        out(out_sidecar)


def set_params_by_tcx(tcxparser, params):
    """
    :param tcxparser: tcxparser
    :param params: PostParams
    :return: True, if successful
    """
    params.set_tcx_data(tcxparser)

    # Updte the post file 'index'

    return False


def copy_tcx(file, force, delete):
    """

    :param file: tcx file to create a post for
    :param force: true to overwrite existing posts
    :param delete: true to delete source file
    :return: post object or False, if skipped
    """
    tcxparser = TCXParser(file)
    date = z_date_to_locale_dt(tcxparser.started_at, tcxparser.latitude, tcxparser.longitude)
    post_dir = build_post_path(date)

    if path.exists(post_dir):
        if force:
            debug(f"removing existing {post_dir}")
            shutil.rmtree(post_dir)

        else:
            debug(f"skipping existing {post_dir}")
            return False

    debug(f"mkdir {post_dir}")
    os.makedirs(post_dir, exist_ok=False)

    post_path = path.join(post_dir, post_file_name)
    shutil.copyfile(post_file_archetype_path, post_path)
    shutil.copyfile(file, path.join(post_dir, path.basename(file)))

    if delete:
        debug("delete source activity file")
        os.remove(file)

    post = read_post_file(post_path)
    # debug(f"post={post}")
    debug(f"tcx={tcxparser}")

    post.set_tcx_data(tcxparser, file)

    # debug(f"post={json.dumps(post.data, indent=2, sort_keys=True)}")
    post.save()

    debug(f"Post created")
    # print(x.strftime("%b %d %Y %H:%M:%S"))
    # out(file)

    return post


def list_files(dir):
    r = []
    subdirs = [x[0] for x in os.walk(dir)]
    for subdir in subdirs:
        files = os.walk(subdir).__next__()[2]
        if len(files) > 0:
            for f in [f for f in files if f.endswith(tcx_suffixes)]:
                r.append(os.path.join(subdir, f))

    return r


def execute_load():
    do_load(args.dir, args.force, args.delete, args.sidecar)


if __name__ == '__main__':
    parse_args()
