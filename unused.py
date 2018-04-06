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

def show_all():
   list_ec2()
   show_ip()
   show_elb()

def list_ec2():
   if args.profile:
      profiles = args.profile.split()
   else:
      profiles = boto3.Session().available_profiles
   for profile in profiles:
      if (not fnmatch(profile, 'default')) and (not fnmatch(profile, '*assumed*')) and not None:
         count = 0
         boto3.setup_default_session(profile_name=profile) 
         if not args.region:
            regions = [region['RegionName'] for region in boto3.client('ec2', region_name='us-west-1').describe_regions()['Regions']]
         else:
            regions = args.region.split()
         ec2_table = PrettyTable(['\033[33mName\033[0m', '\033[33mInstance ID\033[0m', '\033[33mRegion\033[0m', '\033[33mInstance Type\033[0m', '\033[33mPublic IP\033[0m', '\033[33mState\033[0m'])
         for region in regions:
            instances = boto3.resource('ec2', region_name=region).instances.filter()
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
      if (not fnmatch(profile, 'default')) and (not fnmatch(profile, '*assumed*')) and not None:
         count = 0
         boto3.setup_default_session(profile_name=profile) 
         if not args.region:
            regions = [region['RegionName'] for region in boto3.client('ec2', region_name='us-west-1').describe_regions()['Regions']]
         else:
            regions = args.region.split()
         ips_table = PrettyTable(['\033[33mInstance ID\033[0m', '\033[33mPublic IP\033[0m', '\033[33mRegion\033[0m', '\033[33mStatus\033[0m'])
         for region in regions:
            for address in boto3.client('ec2', region_name=region).describe_addresses()['Addresses']:
               if 'NetworkInterfaceId' in address:
                  status = '\033[32mIn used\033[0m'
               else:
                  status = '\033[31mUnused\033[0m'
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


def show_elb():
   if args.profile:
      profiles = args.profile.split()
   else:
      profiles = boto3.Session().available_profiles
   for profile in profiles:
      if (not fnmatch(profile, 'default')) and (not fnmatch(profile, '*assumed*')) and not None:
         count = 0
         boto3.setup_default_session(profile_name=profile)
         if not args.region:
            regions = [region['RegionName'] for region in boto3.client('ec2', region_name='us-east-1').describe_regions()['Regions']]
         else:
            regions = args.region.split()
         elb_table = PrettyTable(['\033[33mName\033[0m', '\033[33mDNS\033[0m', '\033[33mAZs\033[0m', '\033[33mInstances\033[0m'])
         for region in regions:
            for elbs in boto3.client('elb', region_name=region).describe_load_balancers()['LoadBalancerDescriptions']:
               elb_table.add_row([elbs['LoadBalancerName'], elbs['DNSName'], region, len(elbs['Instances'])])
               count += 1
      if count > 0:
         print ('\n\033[93mTables in \033[0m'+profile)
         print elb_table.get_string(sortby='\033[33mName\033[0m')
      else:
         print('\nNo Elastic Load Balancer on '+profile)


def main():
   if args.service == 'ec2':
      list_ec2()
   elif args.service == 'eip':
      show_ip()
   elif args.service == 'elb':
      show_elb()
   else:
      print ('\nGetting all resources. This could take some time')
      show_all()
      
main()
