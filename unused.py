#!/usr/bin/python2.7
import boto3
import sys
import os
import getopt
import botocore.exceptions
import argparse
import re

# ToDo
#  - Multithreading / Multiprocessing
#  - STS

profiles = None
parser = argparse.ArgumentParser()
parser.add_argument('--mail', '-m', default=None, metavar='destiny@mail.com', nargs='?', help='Mail to send report')
args = parser.parse_args()

def check_mail(args):
   if args.mail is not None:
      match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', args.mail)
      if match == None:
         print('\nMail address misspelled.')
         sys.exit(1)

def test_conn(args):
   try:
      ec2 = boto3.client('ec2')
      regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
      s3 = boto3.resource('s3')
      test = s3.buckets.all()
      for region in regions:
         ec2 = boto3.client('ec2', region_name=region)
   except botocore.exceptions.ClientError as ex:
      if ex.response['Error']['Code'] == 'ExpiredToken':
         print('The token seems expired.')
         sys.exit(1)
      elif ex.response['Error']['Code'] == 'AccessDenied':
         print('\nAccess denied')
         sys.exit(1)
      else:
         print('Error unknown. Error : ' + ex.response['Error']['Code'])
         sys.exit(1)
   except botocore.exceptions.NoRegionError:   
      print('\n\033[31mCould not find REGION or DEFAULT_REGION in OS environs.\nWill use "\033[0mus-west-1\033[31m" as default.\033[0m')
      os.environ['AWS_DEFAULT_REGION'] = 'us-west-1'
      os.environ['AWS_REGION'] = 'us-west-1'
   except botocore.exceptions.NoCredentialsError:
      print('\033[31mIt seems your credentials are missing.\033[0m\n')

def main(args):
  if len(sys.argv) == 1:
      print('\n\033[32mMenu\033[0m\n') 
      menu()
  else:
      #try:
         from fnmatch import fnmatch, fnmatchcase
         show_credentials(args)
         list_profiles()
         for profile in boto3.Session().available_profiles:
            if (not fnmatch(profile, 'default')) and (not fnmatch(profile, '*assumed*')):
               boto3.setup_default_session(profile_name=profile)
               show_everything(args)
      #except:

def menu():
   menu = {'1':'[\033[33m1\033[0m] Show everything','2':'[\033[33m2\033[0m] Show credentials','3':'[\033[33m3\033[0m] Show instances stopped','4':'[\033[33m4\033[0m] Show buckets','5':'[\033[33m5\033[0m] Show unused IPs','6':'[\033[33m6\033[0m] Show Elastic LoadBalancer unused'}
   while True: 
     for key, value in (sorted(menu.iteritems())): 
       print(value)
     print('')
     selection = raw_input('Select : ') 
     if selection == '1': 
       show_credentials(args)
       list_profiles()
       show_everything(args)
     elif selection == '2':
       show_credentials(args)
       list_profiles()
     elif selection == '3': 
       show_instances(args)
       instances_temp(args)
     elif selection == '4':
       show_buckets(args)
     elif selection == '5':
       show_ip(args)
     elif selection == '6':
       show_elb(args)
     else: 
       print('Unknown option selected. Exiting...')
       sys.exit(0) # Exiting without errors

def show_everything(args):
      from fnmatch import fnmatch, fnmatchcase
      for profile in boto3.Session().available_profiles:
         if (not fnmatch(profile, 'default')) and (not fnmatch(profile, '*assumed*')):
            print('\033[93mAWS profile \033[0m' + profile)
            boto3.setup_default_session(profile_name=profile)
            show_instances(args)
            instances_temp(args)
            show_ip(args)
            show_elb(args)
            show_buckets(args)

def show_credentials(args):
   try:
      print('\n\033[32mCredentials to be used :\033[0m\n')
      print('\033[31mAWS access key\033[0m ' + boto3.Session().get_credentials().access_key) 
      print('\033[31mAWS secret key\033[0m ' + boto3.Session().get_credentials().secret_key)
      print('\033[31mAWS seesion token\033[0m ' + boto3.Session().get_credentials().token)
      print('\033[31mAWS region name\033[0m ' + boto3.Session().region_name)
   except KeyError: # Do not explode if environs could not be loaded
      print('AWS config not found. Cannot continue without this\n')
      if args.mail is not None:
         print('\033[31mDestination mail address\033[0m ' + args.mail)
      sys.exit(1)
   print('')

def show_instances(args):
   try:
      ec2 = boto3.client('ec2')
      regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
   except botocore.exceptions.ClientError:
      print('\n\033[31mToken expired. Sorry :(\033[0m')
      sys.exit(1)
   print('\n\033[32mShowing stopped instances\033[0m\n')
   for region in regions: 
      conection = boto3.resource('ec2', region_name=region)
      instances = conection.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped','terminated']}])
      for instance in instances:
         if instance is not None:
            if instance.tags is not None:
               for tag in instance.tags:
                  if tag['Key'] == 'Name':
                     print('\033[32mName tag    \033[0m'+tag['Value'])
               print('\033[32mID          \033[0m'+instance.id)
               print('\033[32mType        \033[0m'+instance.instance_type)
               if instance.public_dns_name:
                  print('\033[32mPublic DNA  \033[0m'+instance.public_dns_name)
               print('\033[32mRegion      \033[0m'+region)
               print('---------------------------------------')

def instances_temp(args):
   print('\n\033[32mShowing "tmp" / "temp" / "test" running instances\033[0m\n')
   try:
      ec2 = boto3.client('ec2')
      regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
   except botocore.exceptions.ClientError:
      print('\n\033[31mToken expired. Sorry :(\033[0m')
      sys.exit(1)
   for region in regions:
      conection = boto3.resource('ec2', region_name=region)
      instances = conection.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']},{'Name': 'tag:Name', 'Values': ['*tmp*']},{'Name': 'instance-state-name', 'Values': ['running']},{'Name': 'tag:Name', 'Values': ['*temp*']},{'Name': 'instance-state-name', 'Values': ['running']},{'Name': 'tag:Name', 'Values': ['*test*']}])
      for instance in instances:
         if instance is not None:
            if instance.tags is not None:
               for tag in instance.tags:
                  if tag['Key'] == 'Name':
                     print('\033[32mName tag    \033[0m'+tag['Value'])
               print('\033[32mID          \033[0m'+instance.id)
               print('\033[32mType        \033[0m'+instance.instance_type)
               if instance.public_dns_name:
                  print('\033[32mPublic DNA  \033[0m'+instance.public_dns_name)
               print('\033[32mRegion      \033[0m'+region)
               print('---------------------------------------') 

def show_buckets(args):
   print('\n\033[32mShowing buckets\033[0m\n');
   try:
      s3 = boto3.resource('s3')
      for bucket in s3.buckets.all():
         print('\033[32m- \033[0m'+bucket.name)
      print('')
   except botocore.exceptions.ClientError:
      print('\n\033[31mToken expired. Sorry :(\033[0m')
      sys.exit(1)

def show_ip(args):
   print('\n\033[32mShowing Elastic IPs unused\033[0m\n')
   try:
      client = boto3.client('ec2')
      regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
   except botocore.exceptions.ClientError:
      print('\n\033[31mToken expired. Sorry\033[0m')
      sys.exit(1)
   for region in regions:
      client = boto3.client('ec2', region_name=region)
      adresses = client.describe_addresses()['Addresses']
      for address in adresses:
         if 'NetworkInterfaceId' not in address:
            print(address['PublicIp']+"\033[32m in \033[0m"+region)

def show_elb(args):
   print('\n\033[32mShowing elb\033[0m\n')
   try:
      elb = boto3.client('elb')
      ec2r = boto3.client('ec2')
      lb = elb.describe_load_balancers()
      regions = [region['RegionName'] for region in ec2r.describe_regions()['Regions']]
   except botocore.exceptions.ClientError:
      print('\nToken expired. Sorry :(')
      sys.exit(1)
   for region in regions:
      ec2r = boto3.client('ec2', region_name=region)
      for elbs in lb['LoadBalancerDescriptions']:
         if len(elbs['Instances']) == 0:
            print(elbs['LoadBalancerName']+' in '+region)

def list_profiles():
   print('\033[32mProfiles\033[0m\n')
   sts = boto3.Session()
   for i in sts.available_profiles:
      print(i)
   print('')

if __name__ == '__main__':
   check_mail(args)
   test_conn(args)
   try:
      main(args)
   except KeyboardInterrupt:
      print('')
      print('Ok, ok, quitting...')
      sys.exit(0)
   except botocore.exceptions.NoCredentialsError:
      print('\033[31mIt seems your credentials are missing.\033[0m')
      sys.exit(1)
   except botocore.exceptions.ClientError as ex:
      if ex.response['Error']['Code'] == 'ExpiredToken':
         print('The token seems expired.')
         sys.exit(1)
   except botocore.vendored.requests.exceptions.SSLError:
      print('Connection timed out')
      sys.exit(1)

