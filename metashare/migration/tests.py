'''
Created on 23.07.2012

@author: steffen
'''
import os
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from metashare import settings, test_utils
from metashare.accounts.models import UserProfile
from metashare.repository.models import resourceInfoType_model
from metashare.settings import ROOT_PATH, DJANGO_BASE
from metashare.stats.models import LRStats, QueryStats, UsageStats
from metashare.test_utils import create_user
from metashare.export_node_from_2_1_2_to_2_9 import export_users, export_stats, \
    export_resources
from metashare.storage.models import INGESTED, INTERNAL


def importPublishedFixtures():
    _path = '{}/repository/test_fixtures/pub/'.format(ROOT_PATH)
    files = os.listdir(_path)   
    for filename in files:
        fullpath = os.path.join(_path, filename)  
        test_utils.import_xml_or_zip(fullpath)

class ExportTests(TestCase):
    """
    Test export of data.
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
    
    def test_export(self):
        """
        Test export.
        """

        # test staff users
        admin = create_user('steffen', 'steffen@dfki.de', 'test')
        admin.is_staff = True
        admin.save()
        staffuser = create_user('staffuser', 'staff@example.com', 'secret')
        staffuser.is_staff = True
        staffuser.save()
        # test normal user
        create_user('normaluser', 'normal@example.com', 'secret')
        # export users
        export_users(os.path.join(settings.ROOT_PATH, "dump"))
    
        # import resources    
        importPublishedFixtures()

        # change owner and publication status
        res_1 = resourceInfoType_model.objects.get(pk=1)
        res_1.owners.add(admin, staffuser)
        res_1.save()
        
        res_2 = resourceInfoType_model.objects.get(pk=2)
        res_2.storage_object.publication_status = INGESTED
        # no owner for res_2
        res_2.save()
        
        res_3 = resourceInfoType_model.objects.get(pk=3)
        res_3.storage_object.publication_status = INTERNAL
        res_3.owners.add(staffuser)
        res_3.save()

        # create some stats
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
        
        # export stats
        export_stats(os.path.join(settings.ROOT_PATH, "dump"))
        
        # export resources
        export_resources(os.path.join(settings.ROOT_PATH, "dump"))
