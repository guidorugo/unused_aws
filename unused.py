#!/usr/bin/python2.7
import boto3
import sys
import os
import getopt
import botocore.exceptions

# ToDo
#  - Multithreading / Multiprocessing
#  - STS

def main():
  if len(sys.argv) == 1:  #Just put this for V2
      menu()
  else:
      print('API')

def menu():
   menu = {'1':'[1] Show everything','2':'[2] Show credentials','3':'[3] Show instances stopped','4':'[4] Show buckets','5':'[5] Show unused IPs','6':'[6] Show Elastic LoadBalancer unused'}
   while True: 
     for key, value in (sorted(menu.iteritems())): 
       print(value)
     print('')
     selection = raw_input('Select : ') 
     if selection == '1': 
       show_everything()
     elif selection == '2':
       show_credentials()
     elif selection == '3': 
       show_instances()
       instances_temp()
     elif selection == '4':
       show_buckets()
     elif selection == '5':
       show_ip()
     elif selection == '6':
       show_elb()
     else: 
       print('Unknown option selected. Exiting...')
       sys.exit(0) # Exiting without errors

def show_everything():
   show_credentials()
   show_instances()
   instances_temp()
   show_ip()
   show_elb()
   show_buckets()

def show_credentials():
   try:
      test = os.environ['AWS_PROFILE']
      print('\n\033[32mCredentials to be used :\033[0m\n')
      print('\033[31mAWS access key\033[0m ' + os.environ['AWS_ACCESS_KEY_ID'])
      print('\033[31mAWS secret key\033[0m ' + os.environ['AWS_SECRET_ACCESS_KEY'])
      print('\033[31mAWS session token\033[0m ' + os.environ['AWS_SESSION_TOKEN'])
      print('\033[31mAWS default region\033[0m ' + os.environ['AWS_DEFAULT_REGION'])
      print('\033[31mAWS profile name\033[0m ' + os.environ['AWS_PROFILE'])
   except KeyError: # Do not explode if environs could not be loaded
      print('Environment Variable not found.\n')
      menu()
   try: # ToDo : edit okta-aws to print a timestamp for token expiration
      print('Token created at '+os.environ['AWS_TIMESTAMP'])
   except KeyError:
      pass
   print('')
   list_profiles()
   print('')

def show_instances():
   try:
      ec2 = boto3.client('ec2')
      regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
   except botocore.exceptions.ClientError:
      print('\n\033[31mToken expired. Sorry :(\033[0m')
      sys.exit(1)
   print('\n\033[32mShowing stopped instances (Instances stopped does not charge you)\033[0m\n')
   for region in regions: 
      conection = boto3.resource('ec2', region_name=region)
      instances = conection.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped','terminated']}])
      #print('Instances in '+region)
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

def instances_temp():
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
      #print('Instances in '+region)
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

def show_buckets():
   print('\n\033[32mShowing buckets\033[0m\n');
   try:
      s3 = boto3.resource('s3')
      for bucket in s3.buckets.all():
         print('\033[32m- \033[0m'+bucket.name)
      print('')
   except botocore.exceptions.ClientError:
      print('\n\033[31mToken expired. Sorry :(\033[0m')
      sys.exit(1)

def show_ip():
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

def show_elb():
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

def test_conn():
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
      print('\033[31mCoul not find REGION or DEFAULT_REGION in OS environs.\nWill use "\033[0mus-west-1\033[31m" as default.\033[0m')
      os.environ['AWS_DEFAULT_REGION'] = 'us-west-1'
      os.environ['AWS_REGION'] = 'us-west-1'
   except botocore.exceptions.NoCredentialsError:
      print('\033[31mIt seems your credentials are missing.\033[0m')
      sys.exit(1)

def list_profiles():
   print('\033[32mProfiles\033[0m\n')
   sts = boto3.Session()
   for i in sts.available_profiles:
      print(i)

if __name__ == '__main__':
   test_conn()
   print('\n\033[32mMenu\033[0m\n')
   try:
      main()
   except KeyboardInterrupt:
      print('')
      print('Ok, ok, quitting...')
      sys.exit(0)
