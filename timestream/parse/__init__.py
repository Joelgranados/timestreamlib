#Copyright 2014 Kevin Murray

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
.. module:: timestream.parse
    :platform: Unix, Windows
    :synopsis: Submodule which parses timestream formats.

.. moduleauthor:: Kevin Murray <spam@kdmurray.id.au>
"""

import collections
from datetime import datetime
import glob
from itertools import (
        ifilter,
        imap,
        )
import json
import logging
import os
from os import path

from timestream.parse.validate import (
        validate_timestream_manifest,
        IMAGE_EXT_CONSTANTS,
        IMAGE_EXT_TO_TYPE,
        TS_DATE_FORMAT,
        )
from timestream.util import (
        PARAM_TYPE_ERR,
        dict_unicode_to_str,
        )

#: Default timestream manifest extension
MANIFEST_EXT = ".tsm"
LOG = logging.getLogger(__name__)


def _ts_has_manifest(ts_path):
    """Checks if a timestream has a manifest.

    :param str ts_path: Path to the root of a timestream.
    :returns: The path to the manifest, or ``False``.
    """
    pattern = "{}{}*{}".format(ts_path, os.sep, MANIFEST_EXT)
    manifest = glob.glob(pattern)
    if len(manifest):
        return manifest[0]
    else:
        return False

def ts_parse_date(img):
    basename = path.basename(img)
    fields = basename.split("_")[1:7]
    string_time = "_".join(fields)
    return datetime.strptime(string_time, TS_DATE_FORMAT)

def ts_format_date(dt):
    return dt.strftime(TS_DATE_FORMAT)

def _guess_manifest_info(ts_path):
    """Guesses the values of manifest fields in a timestream
    """
    retval = {}
    # get a sorted list of all files
    all_files = []
    for root, dirs, files in os.walk(ts_path):
        for fle in files:
            all_files.append(path.join(root, fle))
    all_files = sorted(all_files)
    # find most common extension, and assume this is the ext
    exts = collections.Counter(IMAGE_EXT_CONSTANTS)
    our_exts = map(lambda x: path.splitext(x)[1][1:], all_files)
    for ext in our_exts:
        try:
            exts[ext] += 1
        except KeyError:
            pass
    ## most common gives list of tuples. [0] = (ext, count), [0][0] = ext
    retval["extension"] = exts.most_common(1)[0][0]
    # get image type from extension:
    try:
        retval["image_type"] = IMAGE_EXT_TO_TYPE[retval["extension"]]
    except KeyError:
        retval["image_type"] = None
    # Get list of images:
    images = ifilter(
            lambda x: path.splitext(x)[1][1:] == retval["extension"],
            all_files)
    # decode times from images:
    times = map(ts_parse_date, sorted(images))
    # get first and last dates:
    retval["start_datetime"] = ts_format_date(times[0])
    retval["end_datetime"] = ts_format_date(times[-1])
    # Get time intervals between images
    intervals = collections.Counter()
    for iii in range(len(times) - 1):
        interval = times[iii + 1] - times[iii]
        intervals[interval.seconds/60] += 1
    ## most common gives list of tuples. [0] = (ext, count), [0][0] = ext
    retval["interval"] = intervals.most_common(1)[0][0]
    retval["name"] = path.basename(ts_path)
    # This is dodgy isn't it :S
    retval["missing"] = []
    # If any of this worked, it must be version 1
    retval["version"] = 1
    return retval

def _all_files_with_ext(topdir, ext, cs=False):
    """Iterates over all files with extension ``ext`` recursively from ``topdir``
    """
    if not isinstance(topdir, str):
        msg = PARAM_TYPE_ERR.format(param="topdir",
                func="_all_files_with_ext",  type="str")
        LOG.error(msg)
        raise ValueError(msg)
    if not isinstance(ext, str):
        msg = PARAM_TYPE_ERR.format(param="ext",
                func="_all_files_with_ext",  type="str")
        LOG.error(msg)
        raise ValueError(msg)
    if not isinstance(cs, bool):
        msg = PARAM_TYPE_ERR.format(param="cs",
                func="_all_files_with_ext",  type="bool")
        LOG.error(msg)
        raise ValueError(msg)
    # Trim any leading spaces from the extension we've been given
    if ext.startswith("."):
        ext = ext[1:]
    # For speed, we pre-convert the ext to lowercase here if we're being case
    # insensitive
    if not cs:
        ext = ext.lower()
    # OK, walk the dir. we only care about files, hence why dirs never gets
    # touched
    for root, dirs, files in os.walk(topdir):
        for fpath in files:
            # split out ext, and do any case-conversion we need
            fname, fext = path.splitext(fpath)
            if not cs:
                fext = fext.lower()
            # remove the dot at the start, as splitext returns ("fn", ".ext")
            fext = fext[1:]
            if fext == ext:
                # we give the whole path to  the file
                yield path.join(root, fpath)

def _all_files_with_exts(topdir, exts, cs=False):
    """Creates a dictionary of {"ext": [files]} for each ext in exts
    """
    if not isinstance(exts, list):
        LOG.error("Exts must be a list of strings")
        raise ValueError("Exts must be a list of strings")
    ext_dict = {}
    for ext in exts:
        ext_dict[ext] = sorted(list(_all_files_with_ext(topdir, ext, cs)))
    return ext_dict

def get_timestream_manifest(ts_path):
    """Reads in or makes up a manifest for the timestream at ``ts_path``, and
    returns it as a ``dict``
    """
    manifest = _ts_has_manifest(ts_path)
    if manifest:
        with open(manifest) as ifh:
            manifest = json.load(ifh)
        if isinstance(manifest, list):
            # it comes in as a list, we want a dict
            manifest = dict_unicode_to_str(manifest[0])
        manifest = validate_timestream_manifest(manifest)
    else:
        manifest = _guess_manifest_info(ts_path)
    return manifest

def iter_timestream_images(ts_path):
    """Iterate over a ``timestream`` in chronological order
    """
    manifest = get_timestream_manifest(ts_path)

    for fpath in _all_files_with_ext(ts_path, manifest["extension"], cs=False):
        yield fpath

