# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------
"""
Setup script module with _atomic_replace function.
"""

from __future__ import absolute_import, print_function

# Standard library imports
import codecs
import errno
import os
import uuid


def _rename_over_existing(src, dest):
    """
    """
    try:
        # On Windows, this will throw EEXIST, on Linux it won't.
        os.rename(src, dest)
    except IOError as e:
        if e.errno == errno.EEXIST:
            # Clearly this song-and-dance is not in fact atomic,
            # but if something goes wrong putting the new file in
            # place at least the backup file might still be
            # around.
            backup = "{0}.bak-{1}".format(dest, str(uuid.uuid4()))
            os.rename(dest, backup)
            try:
                os.rename(src, dest)
            except Exception as e:
                os.rename(backup, dest)
                raise e
            finally:
                try:
                    os.remove(backup)
                except Exception as e:
                    pass


def atomic_replace(path, contents, encoding):
    """
    """
    tmp = "{0}tmp-{1}".format(path, str(uuid.uuid4()))
    try:
        with codecs.open(tmp, 'w', encoding) as f:
            f.write(contents)
            f.flush()
            f.close()
        _rename_over_existing(tmp, path)
    finally:
        try:
            os.remove(tmp)
        except (IOError, OSError):
            pass
