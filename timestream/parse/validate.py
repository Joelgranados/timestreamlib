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
.. module:: timestream.parse.validate
    :platform: Unix, Windows
    :synopsis: Validate timestream JSON manifests

.. moduleauthor:: Kevin Murray <spam@kdmurray.id.au>
"""

from voluptuous import Schema, Required, Range, All, Length, Any
from timestream.util.validation import (
        v_datetime,
        v_date,
        )

#: Acceptable constants for image filetypes
IMAGE_TYPE_CONSTANTS = ["raw", "jpg", "png"]
#: Acceptable constants indicating that a timestream is full resolution
FULLRES_CONSTANTS = ["fullres"]
#: Acceptable constants 'raw' image format file extensions
RAW_FORMATS = ["cr2", "nef", "tif", "tiff"]
IMAGE_EXT_CONSTANTS = ["jpg", "png"]
IMAGE_EXT_CONSTANTS.extend(RAW_FORMATS)
IMAGE_EXT_CONSTANTS.extend([x.upper() for x in IMAGE_EXT_CONSTANTS])

def validate_timestream_manifest(manifest):
    """Validtes a json manifest, and returns the validated ``dict``

    :param dict manifest: The raw json manifest from ``json.load`` or similar.
    :returns: The validated and type-converted manifest as a ``dict``
    :rtype: dict
    :raises: TypeError, ValueError
    """
    if not isinstance(manifest, dict):
        raise TypeError("Manfiest should be in ``dict`` form.")
    sch = Schema({
        Required("name"): All(str, Length(min=1)),
        Required("version"): All(int, Range(min=1, max=2)),
        Required("start_datetime"): v_datetime,
        Required("end_datetime"): v_datetime,
        Required("image_type"): Any(*IMAGE_TYPE_CONSTANTS),
        Required("extension"): Any(*IMAGE_EXT_CONSTANTS),
        Required("interval", default=1): All(int, Range(min=1)),
        "missing": list,
        })
    try:
        return sch(manifest)
    except Exception as e:
        raise e
        raise ValueError("Manifest is invalid")
