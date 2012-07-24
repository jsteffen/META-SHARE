'''
Created on 23.07.2012

@author: steffen
'''

from StringIO import StringIO
from django.core.serializers import xml_serializer
from metashare.settings import LOG_LEVEL, LOG_HANDLER
import logging
import os
from xml.etree import ElementTree
import shutil

# setup logging
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.migration')
LOGGER.addHandler(LOG_HANDLER)

USERS = "users.xml"
USER_PROFILES = "user-profiles.xml"
LR_STATS = "lr-stats.xml"
QUERY_STATS = "query-stats.xml"
USAGE_STATS = "usage-stats.xml"

class MigrationSerializer(xml_serializer.Serializer):
    """
    Adapted version the replaces the fields options with a skip_fields option
    """
    
    def serialize(self, queryset, **options):
        """
        Serialize a queryset.
        """
        self.options = options

        self.stream = options.pop("stream", StringIO())
        self.skipped_fields = options.pop("skip_fields", None)
        self.use_natural_keys = options.pop("use_natural_keys", False)

        self.start_serialization()
        for obj in queryset:
            self.start_object(obj)
            for field in obj._meta.local_fields:
                if field.serialize:
                    if field.rel is None:
                        if self.skipped_fields is None or not field.attname in self.skipped_fields:
                            self.handle_field(obj, field)
                        else:
                            LOGGER.info("skipping field {}:{}".format(
                              obj.__class__.__name__, field.attname))
                    else:
                        if self.skipped_fields is None or not field.attname[:-3] in self.skipped_fields:
                            self.handle_fk_field(obj, field)
                        else:
                            LOGGER.info("skipping field {}:{}".format(
                              obj.__class__.__name__, field.attname))
            for field in obj._meta.many_to_many:
                if field.serialize:
                    if self.skipped_fields is None or not field.attname in self.skipped_fields:
                        self.handle_m2m_field(obj, field)
                    else:
                        LOGGER.info("skipping field {}:{}".format(
                          obj.__class__.__name__, field.attname))
            self.end_object(obj)
        self.end_serialization()
        return self.getvalue()


def dump_users(dump_folder):
    """
    Dumps user related entities as XML into the given folder.
    """

    from django.contrib.auth.models import User
    from metashare.accounts.models import UserProfile
    
    # create dump folder if required
    _check_folder(dump_folder)

    mig_serializer = MigrationSerializer()
    # serialize users; nothing changes
    _serialize(
      User.objects.all(), 
      os.path.join(dump_folder, "{}".format(USERS)), 
      mig_serializer)
    # serialize user profiles; nothing changes
    _serialize(
      UserProfile.objects.all(), 
      os.path.join(dump_folder, "{}".format(USER_PROFILES)), 
      mig_serializer)
      
      
def dump_stats(dump_folder):
    """
    Dumps statistic related entities as XML into the given folder.
    """

    from metashare.stats.models import LRStats, QueryStats, UsageStats
    
    # create dump folder if required
    _check_folder(dump_folder)
    
    mig_serializer = MigrationSerializer()
    # serialize lr stats; skip ipaddress
    _serialize(
      LRStats.objects.all(), 
      os.path.join(dump_folder, "{}".format(LR_STATS)), 
      mig_serializer, skip_fields=('ipaddress'))
    # serialize query stats; skip ipaddress
    _serialize(
      QueryStats.objects.all(), 
      os.path.join(dump_folder, "{}".format(QUERY_STATS)), 
      mig_serializer, skip_fields=('ipaddress'))
    # serialize usage stats
    _serialize(
      UsageStats.objects.all(), 
      os.path.join(dump_folder, "{}".format(USAGE_STATS)), 
      mig_serializer)


def dump_resources(dump_folder):
    """
    Dumps resources into the given folder using a 'storage' subfolder.
    """
    
    from metashare.repository.models import resourceInfoType_model

    mig_serializer = MigrationSerializer()
    for res in resourceInfoType_model.objects.all():
        _serialize_res(res, dump_folder, mig_serializer)
    


def _check_folder(dump_folder):
    """
    Checks if the given folder exists and creates it if not.
    """
    if not dump_folder.strip().endswith('/'):
        dump_folder = '{0}/'.format(dump_folder)
    _df = os.path.dirname(dump_folder)
    if not os.path.exists(_df):
        os.makedirs(_df)


def _serialize(objects, dump_file, serializer, skip_fields=None):
    """
    Serializes the given objects into the given dump file using the given
    serializer; skips the given fields when serializing.
    """
    out = open(dump_file, "wb")
    serializer.serialize(objects, stream=out, skip_fields=skip_fields)
    out.close()


def _serialize_res(res, folder, serializer):
    """
    Serializes the given resource into the given folder. Uses the given
    serializer to serialize the associated storage object.
    """
    
    from metashare.repository.supermodel import pretty_xml
    from metashare import settings
    
    storage_obj = res.storage_object
    
    target_storage_path = os.path.join(folder, "storage", storage_obj.identifier)
    _check_folder(target_storage_path)
        
    # serialize resource metadata XML 
    root_node = res.export_to_elementtree()
    xml_string = ElementTree.tostring(root_node, encoding="utf-8")
    pretty = pretty_xml(xml_string).encode('utf-8')
    with open(os.path.join(target_storage_path, "metadata.xml"), 'wb') as _out:
        _out.write(pretty)
    
    # serialize associated storage object
    _serialize(
      [storage_obj,], os.path.join(target_storage_path, "storage.xml"), serializer)
    
    # copy possible binaries
    source_storage_path = '{0}/{1}/'.format(settings.STORAGE_PATH, storage_obj.identifier)
    archive_path = os.path.join(source_storage_path, "archive.zip")
    if os.path.isfile(archive_path):
        shutil.copy(
          archive_path, os.path.join(target_storage_path, "archive.zip"))


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