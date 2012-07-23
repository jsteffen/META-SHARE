'''
Created on 23.07.2012

@author: steffen
'''

import os
import sys

# Magic python path, based on http://djangosnippets.org/snippets/281/
from os.path import abspath, dirname, join
parentdir = dirname(dirname(abspath(__file__)))
# Insert our dependencies:
sys.path.insert(0, join(parentdir, 'lib', 'python2.7', 'site-packages'))
# Insert our parent directory (the one containing the folder metashare/):
sys.path.insert(0, parentdir)


def dump_users():

    from django.core import serializers    
    from django.contrib.auth.models import User
    from metashare.accounts.models import UserProfile
    xml_serializer = serializers.get_serializer("xml")()
    out = open("users.xml", "wb")
    xml_serializer.serialize(User.objects.all(), stream=out)
    out.close()
    out = open("user-profiles.xml", "wb")
    xml_serializer.serialize(UserProfile.objects.all(), stream=out)
    out.close()


if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    PROJECT_HOME = os.path.normpath(os.getcwd() + "/..")
    sys.path.append(PROJECT_HOME)