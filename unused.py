#!/usr/bin/python2.7

import boto3
from prettytable import PrettyTable
from operator import itemgetter
from fnmatch import fnmatch, fnmatchcase
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--profile', '-p', metavar='<name>', nargs='?', help='Specify profile')
parser.add_argument('--region', '-r', metavar='<us-east-1>,<eu-west-1>,...', nargs='?', help='Specify region')
parser.add_argument('--service', '-s', metavar='<ec2|rds|s3|all>', nargs='?', help='Service(s) to scrape')
args   = parser.parse_args()

def list_ec2():
   if args.profile:
      profiles = args.profile.split()
   else:
      profiles = boto3.Session().available_profiles
   for profile in profiles:
      count = 0
      if (not fnmatch(profile, 'default')) and (not fnmatch(profile, '*assumed*')) and not None:
         #print ('\nProcessing profile '+profile)
         boto3.setup_default_session(profile_name=profile) 
         if not args.region:
            ec2 = boto3.client('ec2', region_name='us-east-1') 
            regions = [region['RegionName'] for region in boto3.client('ec2', region_name='us-west-1').describe_regions()['Regions']]
         else:
            ec2 = boto3.client('ec2', region_name=args.region)
            regions = args.region.split()
         ec2_table = PrettyTable(['\033[33mName\033[0m', '\033[33mInstance ID\033[0m', '\033[33mRegion\033[0m', '\033[33mInstance Type\033[0m', '\033[33mPublic IP\033[0m', '\033[33mState\033[0m'])
         for region in regions:
            ec2 = boto3.resource('ec2', region_name=region)
            instances = ec2.instances.filter()
            for instance in instances:
               if instance is not None:
                  if instance.state['Name'] == 'pending':
                     state = '\033[33mPending\033[0m'
                  elif instance.state['Name'] == 'running':
                     state = '\033[32mRunning\033[0m'
                  elif instance.state['Name'] == 'shutting-down':
                     state = '\033[91mShutting down\033[0m'
                  elif instance.state['Name'] == 'terminated':
                     state = '\033[31mTerminated\033[0m'
                  elif instance.state['Name'] == 'stopping':
                     state = '\033[34mStopping\033[0m'
                  elif instance.state['Name'] == 'stopped':
                     state = '\033[35mStopped\033[0m'
                  if instance.tags is not None:
                     for tag in instance.tags:                                                                     
                        if 'Name' in tag['Key'] or 'name' in tag['Key']:
                           name = tag['Value']
                        else:
                           name = '-'  
                  ec2_table.add_row([name, instance.instance_id, region, instance.instance_type, instance.public_ip_address, state])
                  count += 1
      if count > 0:
         print('\n\033[93mTables in \033[0m'+profile)
         print ec2_table.get_string(sortby='\033[33mState\033[0m')
      else: 
         print('\nNo instances on '+profile)

def show_ip():
   if args.profile:
      profiles = args.profile.split()
   else:
      profiles = boto3.Session().available_profiles
   for profile in profiles:
      count = 0
      if (not fnmatch(profile, 'default')) and (not fnmatch(profile, '*assumed*')) and not None:
         print ('\nProcessing profile '+profile)
         boto3.setup_default_session(profile_name=profile) 
         if not args.region:
            ec2 = boto3.client('ec2', region_name='us-east-1') 
            regions = [region['RegionName'] for region in boto3.client('ec2', region_name='us-west-1').describe_regions()['Regions']]
         else:
            ec2 = boto3.client('ec2', region_name=args.region)
            regions = args.region.split()
         ips_table = PrettyTable(['\033[33mInstance ID\033[0m', '\033[33mPublic IP\033[0m', '\033[33mRegion\033[0m', '\033[33mStatus\033[0m'])
   #print('\n\033[32mShowing Elastic IPs unused\033[0m\n')
         for region in regions:
            for address in boto3.client('ec2', region_name=region).describe_addresses()['Addresses']:
               if 'NetworkInterfaceId' in address:
                  status = '\033[32mIn used\033[0m'
               else:
                  status = '\033[31mUnused\033[0m'
               #print(address['PublicIp']+"\033[32m in \033[0m"+region)
               if 'InstanceId' not in address:
                  instanceid = '-'
               else:
                  instanceid = address['InstanceId']
               ips_table.add_row([instanceid, address['PublicIp'], region, status])
               count += 1
      if count > 0:
         print ('\033[93mTables in \033[0m'+profile)
         print ips_table.get_string(sortby='\033[33mStatus\033[0m')
      else:
         print('\nNo Elastic IPs on '+profile)

def main():
   if args.service == 'ec2':
      list_ec2()
   elif args.service == 'eip':
      show_ip()
   #elif args.service == 'ec2':
   #   scrape_ec2(region, args.label)
   #elif args.service == 'rds':
   # scrape_rds(region, args.label)
   #elif args.service == 's3':
   # scrape_s3(region, args.label)
   #elif args.service == 'all':
   # scrape_ebs(region, args.label)
   # scrape_ec(region, args.label)
   # scrape_ec2(region, args.label)
   # scrape_rds(region, args.label)
   # scrape_s3(region, args.label)
   #else:
   # exit('Service to scrape not valid or not defined: "{0}".'.format(args.service))

main()
