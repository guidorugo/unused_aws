#!/usr/bin/python

import boto3
import sys
import os
import datetime
import sys
import getopt
import csv
from botocore.exceptions import ClientError

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
       show_ip()
       show_elb()
       show_buckets()
     elif selection == '3': 
       show_instances()
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
      print('AWS access key ',os.environ['AWS_ACCESS_KEY_ID'])
      print('AWS secret key ',os.environ['AWS_SECRET_ACCESS_KEY'])
      print('AWS session token ',os.environ['AWS_SESSION_TOKEN'])
      print('AWS default region ',os.environ['AWS_DEFAULT_REGION'])
      print('AWS profile name ',os.environ['AWS_PROFILE'])
   except KeyError:
      print('Environment Variable not found')
      menu() # ToDo add other credential info
   try:
      print('Token created at ',os.environ['AWS_TIMESTAMP'])
   except KeyError:
      pass
   print('')

def show_instances():
   print('')
   print('Showing stopped instances')
   ec2 = boto3.client('ec2')
   regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
   for region in regions: 
      conection = boto3.resource('ec2', region_name=region)
      instances = conection.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped','terminated']}])
      for instance in instances:
         print('')
         for tag in instance.tags:
            if tag['Key'] == 'Name':
               print('Name tag : ',tag['Value'])
         print('ID : ',instance.id)
         print('type : ',instance.instance_type)
         if instance.public_dns_name:
            print('Public DNA : '+instance.public_dns_name)
         print("Region : ",region)
         print('------------------------------')
 
def show_buckets():
   print('')
   print('Showing buckets');
   print('')
   s3 = boto3.resource('s3')
   for bucket in s3.buckets.all():
      print('- ',bucket.name)
   print('')

def show_ip():
   print('')
   print('Showing Elastic IPs unused')
   print('')
   count = 0
   client = boto3.client('ec2')
   regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
   for region in regions:
      client = boto3.client('ec2', region_name=region)
      adresses = client.describe_addresses()['Addresses']
      for address in adresses:
         if 'NetworkInterfaceId' not in address:
            print(address['PublicIp']," in ",region)
            count += 1
      if count == '0':
         print('No Elastic IPs unused found.')



def show_elb():
   print('')   
   print('Showing elb')
   print('')
   elb = boto3.client('elb')
   ec2r = boto3.client('ec2')
   lb = elb.describe_load_balancers()
   regions = [region['RegionName'] for region in ec2r.describe_regions()['Regions']]
   for region in regions:
      ec2r = boto3.client('ec2', region_name=region)
      for elbs in lb['LoadBalancerDescriptions']:
         if len(elbs['Instances']) == 0:
            print(elbs['LoadBalancerName'],' in ',region)

def test_conn():
   try:
      test = boto3.resource('s3')
   except ClientError:
      print('There is an issue with the credentials')
      sys.exit(1)

if __name__ == '__main__':
   import argparse
   parser = argparse.ArgumentParser()
   parser.add_argument('--service', default='all', metavar='<ebs|ec|ec2|rds|s3|all>', nargs='?', help='Service(s) to scrape')
   parser.add_argument('--region', default='all', metavar='<us-east-1>,<eu-west-1>,<...>', nargs='?', help='AWS Region')
   parser.add_argument('--output', default='all', metavar='<table|csv|all>', nargs='?', help='Output format')
   parser.add_argument('-q', '--quiet', action='store_false', dest='verbose', default=True, help='Show as minimum as possible')
   args = parser.parse_args()
   test_conn()
   #parser = argparse.ArgumentParser()
   if args.verbose:
      print('\nMenu\n')
   try:
      main()
   except KeyboardInterrupt:
      print('')
      print('Ok, ok, quitting...')
      sys.exit(0)
