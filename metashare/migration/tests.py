'''
Created on 23.07.2012

@author: steffen
'''
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from metashare import settings, test_utils
from metashare.accounts.models import UserProfile
from metashare.migration.migration_utils import dump_users, load_users, \
    dump_stats, load_stats
from metashare.repository.models import resourceInfoType_model
from metashare.settings import ROOT_PATH, DJANGO_BASE
from metashare.stats.models import LRStats, QueryStats, UsageStats
from metashare.test_utils import create_user
import os


class SerializeTests(TestCase):
    """
    Test serialization of data.
    """
    
    def setUp(self):
        test_utils.setup_test_storage()
    
    def tearDown(self):
        resourceInfoType_model.objects.all().delete()
        User.objects.all().delete()
        UserProfile.objects.all().delete()
        LRStats.objects.all().delete()
        QueryStats.objects.all().delete()
        UsageStats.objects.all().delete()

    @classmethod
    def importPublishedFixtures(cls):
        _path = '{}/repository/test_fixtures/pub/'.format(ROOT_PATH)
        files = os.listdir(_path)   
        for filename in files:
            fullpath = os.path.join(_path, filename)  
            test_utils.import_xml_or_zip(fullpath)
    
    def test_users(self):
        """
        Serialize user related entities.
        """

        # test staff user
        staffuser = create_user('staffuser', 'staff@example.com', 'secret')
        staffuser.is_staff = True
        staffuser.save()
        # test normal user
        create_user('normaluser', 'normal@example.com', 'secret')
        # dump
        dump_users(os.path.join(settings.ROOT_PATH, "dump"))
        
        
    def test_stats(self):
        """
        Serialize stats related entities.
        """
        SerializeTests.importPublishedFixtures()

        # search
        client = Client()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True,
          data={'q':'Italian'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
        # view
        url = '/{0}repository/browse/1/'.format(DJANGO_BASE)
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/lr_view.html') 
        
        # dump
        dump_stats(os.path.join(settings.ROOT_PATH, "dump"))
        
        
class DeserializeTests(TestCase):
    """
    Test deserialization of data.
    """
    
    def setUp(self):
        test_utils.setup_test_storage()
    
    def tearDown(self):
        resourceInfoType_model.objects.all().delete()
        User.objects.all().delete()
        UserProfile.objects.all().delete()
        LRStats.objects.all().delete()
        QueryStats.objects.all().delete()
        UsageStats.objects.all().delete()
        
    def test_users(self):
        """
        Deserialize user related entities.
        """
        self.assertEquals(0, len(User.objects.all()))
        self.assertEquals(0, len(UserProfile.objects.all()))
        load_users(os.path.join(settings.ROOT_PATH, "dump"))
        self.assertEquals(2, len(User.objects.all()))
        self.assertEquals(2, len(UserProfile.objects.all()))
        
    def test_stats(self):
        """
        Deserialize stats related entities.
        """
        self.assertEquals(0, len(LRStats.objects.all()))
        self.assertEquals(0, len(QueryStats.objects.all()))
        self.assertEquals(0, len(UsageStats.objects.all()))
        load_stats(os.path.join(settings.ROOT_PATH, "dump"))
        self.assertEquals(4, len(LRStats.objects.all()))
        self.assertEquals(1, len(QueryStats.objects.all()))
        self.assertEquals(127, len(UsageStats.objects.all()))
