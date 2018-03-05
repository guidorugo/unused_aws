#!/usr/bin/python

import boto3
import sys
import os
import sys
import getopt
import botocore.exceptions

# ToDo
#  - Multithreading / Multiprocessing
#  - STS

def main():
  if len(sys.argv) == 1:  
      menu()
  else:
      print('API')

def menu():
   menu = {'1':'[1] Show credentials','2':'[2] Show everything','3':'[3] Show instances stopped','4':'[4] Show buckets','5':'[5] Show unused IPs','6':'[6] Show Elastic LoadBalancer unused'}
   while True: 
     for key, value in (sorted(menu.iteritems())): 
       print(value)
     print('')
     selection = raw_input('Please Select : ') 
     if selection == '1': 
       show_credentials()
     elif selection == '2':
       show_instances()
       instances_temp()
       show_ip()
       show_elb()
       show_buckets()
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
       print "Unknown option selected. Exiting..."
       sys.exit(0) 

def show_credentials(): # Printing credentials into
   try:
      print('\nCredentials to be used :')
      print('AWS access key '+os.environ['AWS_ACCESS_KEY_ID'])
      print('AWS secret key '+os.environ['AWS_SECRET_ACCESS_KEY'])
      print('AWS session token '+os.environ['AWS_SESSION_TOKEN'])
      print('AWS default region '+os.environ['AWS_DEFAULT_REGION'])
      print('AWS profile name '+os.environ['AWS_PROFILE'])
   except KeyError:
      print('Environment Variable not found.')
      menu() # ToDo add other credential info
   try:
      print('Token created at '+os.environ['AWS_TIMESTAMP'])
   except KeyError:
      pass
   print('')

def show_instances():
   try:
      ec2 = boto3.client('ec2')
      regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
   except botocore.exceptions.ClientError:
      print('\nToken expired. Sorry :(')
      sys.exit(1)
   print('\nShowing stopped instances (Instances stopped does not charge you)')
   for region in regions: 
      conection = boto3.resource('ec2', region_name=region)
      instances = conection.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped','terminated']}])
      print('Instances in '+region)
      for instance in instances:
         print('')
         if instance is not None:
            if instance.tags is not None:
               for tag in instance.tags:
                  if tag['Key'] == 'Name':
                     print('Name tag   : '+tag['Value'])
               print('ID         : '+instance.id)
               print('type       : '+instance.instance_type)
               if instance.public_dns_name:
                  print('Public DNA : '+instance.public_dns_name)
               print('---------------------------------------')

def instances_temp():
   print('\n---------- Showing "tmp" / "temp" / "test" running instances ----------\n')
   try:
      ec2 = boto3.client('ec2')
      regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
   except botocore.exceptions.ClientError:
      print('\nToken expired. Sorry :(')
      sys.exit(1)
   for region in regions:
      conection = boto3.resource('ec2', region_name=region)
      instances = conection.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']},{'Name': 'tag:Name', 'Values': ['*tmp*']},{'Name': 'instance-state-name', 'Values': ['running']},{'Name': 'tag:Name', 'Values': ['*temp*']},{'Name': 'instance-state-name', 'Values': ['running']},{'Name': 'tag:Name', 'Values': ['*test*']}])
      print('Instances in '+region)
      for instance in instances:
         if instance is not None:
            if instance.tags is not None:
               for tag in instance.tags:
                  if tag['Key'] == 'Name':
                     print('Name tag   : '+tag['Value'])
               print('ID         : '+instance.id)
               print('type       : '+instance.instance_type)
               if instance.public_dns_name:
                  print('Public DNA : '+instance.public_dns_name)
               print('---------------------------------------') 

def show_buckets():
   print('\nShowing buckets\n');
   try:
      s3 = boto3.resource('s3')
      for bucket in s3.buckets.all():
         print('- '+bucket.name)
      print('')
   except botocore.exceptions.ClientError:
      print('\nToken expired. Sorry :(')
      sys.exit(1)

def show_ip():
   print('\nShowing Elastic IPs unused\n')
   try:
      client = boto3.client('ec2')
      regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
   except botocore.exceptions.ClientError:
      print('\nToken expired. Sorry')
      sys.exit(1)
   for region in regions:
      client = boto3.client('ec2', region_name=region)
      adresses = client.describe_addresses()['Addresses']
      for address in adresses:
         if 'NetworkInterfaceId' not in address:
            print(address['PublicIp']+" in "+region)

def show_elb():
   print('\nShowing elb\n')
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
      s2 = boto3.resource('s3')
      ec2 = boto3.client('ec2')
      regions = [region['RegionName'] for region in ec2r.describe_regions()['Regions']]
      elb = boto3.client('elb')
   except botocore.exceptions.ClientError:
      print('There is an issue with the credentials. Probably with the token.')
      sys.exit(1)
   except botocore.exceptions.NoRegionError:   
      print('There is an issue with the region. I coul not find REGION or DEFAULT_REGION.\nI will use "us-west-1" as default.')
      os.environ['AWS_DEFAULT_REGION'] = 'us-west-1'
      os.environ['AWS_REGION'] = 'us-west-1'

if __name__ == '__main__':
   test_conn()
   print('\nMenu\n')
   try:
      main()
   except KeyboardInterrupt:
      print('')
      print('Ok, ok, quitting...')
      sys.exit(0)
