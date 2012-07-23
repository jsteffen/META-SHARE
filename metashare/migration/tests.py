'''
Created on 23.07.2012

@author: steffen
'''
from django.test import TestCase
from metashare.test_utils import create_user
from metashare.migration.migration_utils import dump_users


class UserDumpTest(TestCase):
    """
    Test dumping of user related entities.
    """
    
    def test_dump(self):

        # test staff user
        staffuser = create_user('staffuser', 'staff@example.com', 'secret')
        staffuser.is_staff = True
        staffuser.save()
        # test normal user
        create_user('normaluser', 'normal@example.com', 'secret')
        # dump
        dump_users()