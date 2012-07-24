'''
Created on 23.07.2012

@author: steffen
'''

from os.path import abspath, dirname, join
import os
import sys

# Magic python path, based on http://djangosnippets.org/snippets/281/
parentdir = dirname(dirname(abspath(__file__)))
# Insert our dependencies:
sys.path.insert(0, join(parentdir, 'lib', 'python2.7', 'site-packages'))
# Insert our parent directory (the one containing the folder metashare/):
sys.path.insert(0, parentdir)


USERS = "users"
USER_PROFILES = "user-profiles"
LR_STATS = "lr-stats"
QUERY_STATS = "query-stats"
USAGE_STATS = "usage-stats"

MIGRATION_FORMAT = "xml"

def dump_users(dump_folder):
    """
    Dumps user related entities as XML into the given folder.
    """

    from django.core import serializers    
    from django.contrib.auth.models import User
    from metashare.accounts.models import UserProfile
    
    # create dump folder if required
    _check_dump_folder(dump_folder)

    xml_serializer = serializers.get_serializer(MIGRATION_FORMAT)()
    # serialize users
    _serialize(
      User.objects.all(), 
      os.path.join(dump_folder, "{}.{}".format(USERS, MIGRATION_FORMAT)), 
      xml_serializer)
    # serialize user profiles
    _serialize(
      UserProfile.objects.all(), 
      os.path.join(dump_folder, "{}.{}".format(USER_PROFILES, MIGRATION_FORMAT)), 
      xml_serializer)
      
      
def dump_stats(dump_folder):
    """
    Dumps statistic related entities as XML into the given folder.
    """

    from django.core import serializers
    from metashare.stats.models import LRStats, QueryStats, UsageStats
    
    # create dump folder if required
    _check_dump_folder(dump_folder)
    
    xml_serializer = serializers.get_serializer(MIGRATION_FORMAT)()
    # serialize lr stats
    _serialize(
      LRStats.objects.all(), 
      os.path.join(dump_folder, "{}.{}".format(LR_STATS, MIGRATION_FORMAT)), 
      xml_serializer)
    # serialize query stats
    _serialize(
      QueryStats.objects.all(), 
      os.path.join(dump_folder, "{}.{}".format(QUERY_STATS, MIGRATION_FORMAT)), 
      xml_serializer)
    # serialize usage stats
    _serialize(
      UsageStats.objects.all(), 
      os.path.join(dump_folder, "{}.{}".format(USAGE_STATS, MIGRATION_FORMAT)), 
      xml_serializer)


def _check_dump_folder(dump_folder):
    """
    Checks if the given folder exists and creates it if not.
    """
    if not dump_folder.strip().endswith('/'):
        dump_folder = '{0}/'.format(dump_folder)
    _df = os.path.dirname(dump_folder)
    if not os.path.exists(_df):
        os.makedirs(_df)


def _serialize(objects, dump_file, serializer):
    """
    Serializes the given objects into the given dump file using the given
    serializer.
    """
    out = open(dump_file, "wb")
    serializer.serialize(objects, stream=out)
    out.close()


def load_users(dump_folder):
    """
    Loads user related entities from XML in the given folder.
    """
    # load users
    _load(os.path.join(dump_folder, "{}.{}".format(USERS, MIGRATION_FORMAT)))
    # load user profiles
    _load(os.path.join(dump_folder, "{}.{}".format(USER_PROFILES, MIGRATION_FORMAT)))


def load_stats(dump_folder):
    """
    Loads statistic related entities from XML in the given folder.
    """
    # load lr stats
    _load(os.path.join(dump_folder, "{}.{}".format(LR_STATS, MIGRATION_FORMAT)))
    # load query stats
    _load(os.path.join(dump_folder, "{}.{}".format(QUERY_STATS, MIGRATION_FORMAT)))
    # load usage stats
    _load(os.path.join(dump_folder, "{}.{}".format(USAGE_STATS, MIGRATION_FORMAT)))
    

def _load(dump_file):
    """
    Loads the objects from the given dump file and saves them in the database.
    """
    from django.core import serializers    
    
    _in = open(dump_file, "rb")
    for obj in serializers.deserialize(MIGRATION_FORMAT, _in):
        _obj = obj.object
        _obj.save()
    _in.close()
    

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    PROJECT_HOME = os.path.normpath(os.getcwd() + "/..")
    sys.path.append(PROJECT_HOME)