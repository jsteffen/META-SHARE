#!/usr/bin/env python
"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import os
import sys
import logging
from metashare.settings import LOG_LEVEL, LOG_HANDLER


# Magic python path, based on http://djangosnippets.org/snippets/281/
from os.path import abspath, dirname, join
parentdir = dirname(dirname(abspath(__file__)))
# Insert our dependencies:
sys.path.insert(0, join(parentdir, 'lib', 'python2.7', 'site-packages'))
# Insert our parent directory (the one containing the folder metashare/):
sys.path.insert(0, parentdir)


try:
    import settings # Assumed to be in the same directory.

except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the " \
      "directory containing %r. It appears you've customized things.\n" \
      "You'll have to run django-admin.py, passing it your settings " \
      "module.\n(If the file settings.py does indeed exist, it's causing" \
      " an ImportError somehow.)\n" % __file__)
    sys.exit(1)

# setup logging
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.migration')
LOGGER.addHandler(LOG_HANDLER)

USERS = "users.xml"
USER_PROFILES = "user-profiles.xml"
LR_STATS = "lr-stats.xml"
QUERY_STATS = "query-stats.xml"
USAGE_STATS = "usage-stats.xml"


def load_users(dump_folder):
    """
    Loads user related entities from XML in the given folder.
    """
    # load users
    _load(os.path.join(dump_folder, "{}".format(USERS)))
    # load user profiles
    _load(os.path.join(dump_folder, "{}".format(USER_PROFILES)))


def load_stats(dump_folder):
    """
    Loads statistic related entities from XML in the given folder.
    """
    # load lr stats
    _load(os.path.join(dump_folder, "{}".format(LR_STATS)))
    # load query stats
    _load(os.path.join(dump_folder, "{}".format(QUERY_STATS)))
    # load usage stats
    _load(os.path.join(dump_folder, "{}".format(USAGE_STATS)))
    

def _load(dump_file):
    """
    Loads the objects from the given dump file and saves them in the database.
    """
    from django.core import serializers    
    
    _in = open(dump_file, "rb")
    for obj in serializers.deserialize("xml", _in):
        _obj = obj.object
        _obj.save()
    _in.close()

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    PROJECT_HOME = os.path.normpath(os.getcwd() + "/..")
    sys.path.append(PROJECT_HOME)
    
    # Check command line parameters first.
    if len(sys.argv) < 2:
        print "\n\tusage: {0} <source-folder>\n".format(sys.argv[0])
        sys.exit(-1)

    load_users(sys.argv[1])
    load_stats(sys.argv[1])
