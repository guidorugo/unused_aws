#!/usr/bin/python2.7

import boto3
from prettytable import PrettyTable
from operator import itemgetter
from fnmatch import fnmatch, fnmatchcase
import argparse
import datetime
import botocore.exceptions
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--profile', '-p', metavar='<name>', nargs='?', help='Specify profile')
parser.add_argument('--region', '-r', metavar='<us-east-1>,<eu-west-1>,...', nargs='?', help='Specify region')
parser.add_argument('--service', '-s', metavar='<ec2|rds|s3|all>', nargs='?', help='Service(s) to scrape')
args   = parser.parse_args()

def show_all():
    print ('Getting resources. This could take some time')
    list_ec2()
    show_ip()
    show_elb()
    list_s3()

def list_ec2():
    if args.profile:
        profiles = args.profile.split()
    else:
        profiles = boto3.Session().available_profiles
    for profile in profiles:
        try:
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
        except botocore.exceptions.ClientError as ex:
            if ex.response['Error']['Code'] == 'UnauthorizedOperation':
                pass
            elif ex.response['Error']['Code'] == 'AccessDenied':
                print('\nUnauthorized operation. Skipping profile '+profile)
                pass
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
            print ('\n\033[93mTables in \033[0m'+profile)
            print ips_table.get_string(sortby='\033[33mStatus\033[0m')
        else:
            print('\nNo Elastic IPs on '+profile)

def show_elb():
    if args.profile:
        profiles = args.profile.split()
    else:
        profiles = boto3.Session().available_profiles
    for profile in profiles:
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

def list_s3():
    if args.profile:
        profiles = args.profile.split()
    else:
        profiles = boto3.Session().available_profiles
    for profile in profiles:
        count = 0
        #print ('\nProcessing profile '+profile)
        boto3.setup_default_session(profile_name=profile)
        s3_table = PrettyTable(['\033[33mName\033[0m', '\033[33mSize (Gb)\033[0m', '\033[33mCreation\033[0m'])
        for s3_bucket in boto3.client('s3').list_buckets()['Buckets']:
            s3_bucket_creation_date = s3_bucket['CreationDate'].isoformat()
            bucket_size = boto3.client('cloudwatch', region_name='us-east-1').get_metric_statistics(Namespace='AWS/S3', MetricName='BucketSizeBytes', StartTime=(datetime.datetime.utcnow().replace(microsecond=0) - datetime.timedelta(days=14)).isoformat(),EndTime=datetime.datetime.utcnow().replace(microsecond=0).isoformat(), Period=1800, Statistics=["Average"], Dimensions=[{ 'Name': 'StorageType', 'Value': 'StandardStorage'},{'Name': 'BucketName','Value': s3_bucket['Name']}])
            try:
                bucket_size_datapoints = bucket_size['Datapoints']
                bucket_size_last_datapoint = sorted(bucket_size_datapoints, key=itemgetter('Timestamp'))[-1]
                bucket_size_avg = round(bucket_size_last_datapoint['Average']/(1024*1024*1024), 2)
            except IndexError:
                bucket_size_avg = "N/A"
            #print bucket_size_avg, s3_bucket['Name']
            s3_table.add_row([s3_bucket['Name'], bucket_size_avg, s3_bucket['CreationDate'].date()])
            count += 1
        if count > 0:
            print('\n\033[93mBuckets in \033[0m'+profile)
            print s3_table.get_string(sortby='\033[33mName\033[0m')
        else: 
            print('\nNo buckets on '+profile)

def main():
    if args.service == 'ec2':
        list_ec2()
    elif args.service == 'eip':
        show_ip()
    elif args.service == 'elb':
        show_elb()
    elif args.service == 's3':
        list_s3()
    else:
        show_all()

def test_con():
    print('Testing connection and credentials.\n')
    error = False
    try:
        test = boto3.client('s3').list_buckets()
    except botocore.exceptions.ClientError as ex:
        if ex.response['Error']['Code'] == 'ExpiredToken':
            print('\n\033[31mThe token seems expired.\033[0m')
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
        error = True
        test_con()
    except botocore.exceptions.NoCredentialsError:
        print('\033[31mIt seems your credentials are missing.\033[0m\n')
        error = True
        
try:
    test_con()
    main()
except KeyboardInterrupt:
    print('')
    print('Ok, ok, quitting...')
    sys.exit(0)
except botocore.vendored.requests.exceptions.SSLError:
    print('Connection timed out')