import boto3
import sys
import os
import datetime

ec2 = boto3.resource('ec2')
s3 = boto3.resource('s3')
vpc = ec2.Vpc('id')

def show_credentials(): # Printing credentials into
   print('')
   print('\nCredentials used :')
   print('AWS access key '+os.environ['AWS_ACCESS_KEY_ID'])
   print('AWS secret key '+os.environ['AWS_SECRET_ACCESS_KEY'])
   print('AWS session token '+os.environ['AWS_SESSION_TOKEN'])
   print('AWS region '+os.environ['AWS_DEFAULT_REGION'])
   print('AWS profile name '+os.environ['AWS_PROFILE'])
   print('Token created at '+os.environ['AWS_TIMESTAMP'])
   print('\n')

def show_instances():
   print('')
   print('Showing stopped instances')
   print('')
   instances = ec2.instances.filter(Filters=[{'Name':'instance-state-name','Values':['stopped','terminated']}])
   for instance in instances:
      print('')
      for tag in instance.tags:
         if tag['Key'] == 'Name':
            print('Name tag : '+tag['Value'])
      print('ID : '+instance.id)
      print('type : '+instance.instance_type)
      if instance.public_dns_name:
         print('Public DNA : '+instance.public_dns_name)
      #print('State : '+instance.state['Name'])
      print('------------------------')
   
def show_buckets():
   print('')
   print('Showing buckets');
   print('_____________________')
   print('')
   for bucket in s3.buckets.all():
      print(bucket.name)

def show_ip():
   print('')
   print('Showing Elastic IPs')
   print('')
   client = boto3.client('ec2')
   adresses = client.describe_addresses()
   for address in adresses['Addresses']:
      if 'NetworkInterfaceId' not in address:
         print(address['PublicIp'])
   
if __name__ == '__main__':
   #show_credentials()
   show_instances()
   show_buckets()
   show_ip()

