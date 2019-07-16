import boto3
import requests
import logging
import sys
import os
from botocore.exceptions import ClientError

domains = os.getenv('ROUTE53_DOMAINS')
client = boto3.client('route53')


def get_public_ip():
    logging.info('Fetching Public IP Address...')
    try:
        response = requests.get('https://wtfismyip.com/text')
    except requests.exceptions.RequestException as e:
        logging.debug(e)
        logging.info('Failed to get IP, exiting.')
        sys.exit(1)
    if response.status_code == 200:
        public_ip = response.text.rstrip()
        logging.info('Returning IP: %s', public_ip)
    else:
        logging.info('Failed to get IP, exiting.')
        sys.exit(1)
    return public_ip


def update_A_records(client, domains, public_ip):
    domainlist = []
    for domain in domains.split(','):
        domain = domain.rstrip()
        if domain != '':
            domainlist.append(domain)
    if len(domainlist) > 0:
        logging.info('Updating domains: %s', domainlist)
        for domain_name in domainlist:
            try:
                hosted_zone_id = 'ZXGSJDWC4EE3G'
            except ClientError as e:
                logging.debug(e)
            try:
                response = client.change_resource_record_sets(
                    HostedZoneId=hosted_zone_id,
                    ChangeBatch={
                        "Comment": "Automatic DNS update",
                        "Changes": [
                            {
                                "Action": "UPSERT",
                                "ResourceRecordSet": {
                                    "Name": domain_name,
                                    "Type": "A",
                                    "TTL": 60,
                                    "ResourceRecords": [
                                        {
                                            "Value": public_ip
                                        },
                                    ],
                                }
                            },
                        ]
                    }
                )
                logging.info(response)
            except ClientError as e:
                logging.debug(e)
    else:
        logging.info(
            'No domains listed in environment variable ROUTE53_DOMAINS.')


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    public_ip = get_public_ip()
    update_A_records(client, domains, public_ip)
