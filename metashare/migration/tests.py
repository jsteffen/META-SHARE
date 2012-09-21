'''
Created on 23.07.2012

@author: steffen
'''
import os
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from metashare import settings, test_utils
from metashare.accounts.models import UserProfile, Organization,\
    OrganizationManagers, EditorGroup, EditorGroupManagers
from metashare.repository.models import resourceInfoType_model
from metashare.settings import ROOT_PATH, DJANGO_BASE
from metashare.stats.models import LRStats, QueryStats, UsageStats
from metashare.test_utils import create_user, clean_resources_db, clean_user_db
from metashare.export_node_from_2_9_beta_to_3_0 import export_users, export_stats, \
    export_resources
from metashare.storage.models import INGESTED, INTERNAL
import shutil


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
        clean_resources_db()
        clean_user_db()
        LRStats.objects.all().delete()
        QueryStats.objects.all().delete()
        UsageStats.objects.all().delete()
    
    def test_export(self):
        """
        Test export.
        """

        # super user
        admin = create_user('admin', 'admin@example.com', 'secret')
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        
        # staff user
        staffuser = create_user('staffuser', 'staff@example.com', 'secret')
        staffuser.is_staff = True
        staffuser.save()
        
        # normal user
        create_user('normaluser', 'normal@example.com', 'secret')
        
        # organizations
        test_organization = Organization.objects.create(
          name='test_organization')
        test_organization2 = Organization.objects.create(
          name='test_organization2')
        
        # editor groups
        test_editor_group = EditorGroup.objects.create(
          name='test_editor_group')
        test_editor_group2 = EditorGroup.objects.create(
          name='test_editor_group2')
          
        # organization managers
        test_organization_managers = \
          test_utils.create_organization_manager_user(
            'test_organization_manager', 'orgman1@example.com','secret', 
            groups=(test_organization,))
        test_organization_managers2 = \
          test_utils.create_organization_manager_user(
            'test_organization_manager2', 'orgman2@example.com', 'secret',
            groups=(test_organization2,))
            
        # organization members
        org_member_1 = test_utils.create_organization_member(
          'org_member1', 'orgmember1@example.com', 'secret', 
          groups=(test_organization,))
        org_member_2 = test_utils.create_organization_member(
          'org_member2', 'org_member2@example.com', 'secret',
          groups=(test_organization2, test_editor_group2))
          
        # editor group manager
        test_editor_group_manager = test_utils.create_manager_user(
          'ed_manager1', 'edmanager1@example.com', 'secret',
          groups=(test_editor_group,))
        test_editor_group_manager2 = test_utils.create_manager_user(
          'ed_manager2', 'edmanager2@example.com', 'secret',
          groups=(test_editor_group2,))

        # editor group members
        ed_member_1 = test_utils.create_editor_user(
          'ed_user', 'eduser@example.com', 'secret',
          groups=(test_editor_group,))
        ed_member_2 = test_utils.create_editor_user(
          'ed_user2', 'eduser2@example.com', 'secret',
          groups=(test_editor_group2, test_organization2))
        
        # export users
        export_users(os.path.join(settings.ROOT_PATH, "dump"))
    
        # import resources    
        importPublishedFixtures()

        # change owner and publication status
        res_1 = resourceInfoType_model.objects.get(pk=1)
        res_1.owners.add(admin, staffuser, org_member_1, ed_member_1, test_organization_managers)
        res_1.storage_object.checksum = "3930f5022aff02c7fa27ffabf2eaaba0"
        shutil.copyfile(
          '{0}/repository/fixtures/archive.zip'.format(settings.ROOT_PATH),
          '{0}/{1}/archive.zip'.format(
            settings.STORAGE_PATH, res_1.storage_object.identifier))
        res_1.save()
        
        res_2 = resourceInfoType_model.objects.get(pk=2)
        res_2.storage_object.publication_status = INGESTED
        # no owner for res_2
        res_2.save()
        
        res_3 = resourceInfoType_model.objects.get(pk=3)
        res_3.storage_object.publication_status = INTERNAL
        res_3.owners.add(staffuser, org_member_2, ed_member_2, test_editor_group_manager)
        res_3.save()

        # create some stats
        # search
        client = Client()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True,
          data={'q':'Mandarin'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
        # view
        url = res_1.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/lr_view.html') 
        
        # export stats
        export_stats(os.path.join(settings.ROOT_PATH, "dump"))
        
        # export resources
        export_resources(os.path.join(settings.ROOT_PATH, "dump"))