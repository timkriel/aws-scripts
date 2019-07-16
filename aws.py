import boto3
import logging


def loop_through_regions():
    client = boto3.client('ec2')
    report = []
    for region in client.describe_regions()['Regions']:
        logging.info('querying aws region %s', region)
        region_report = {}
        ec2 = boto3.resource('ec2', region_name=region['RegionName'])
        region_report.update(get_unattached_volumes(ec2))
        region_report.update(get_unscheduled_snapshots(ec2))
        if len(region_report) > 0:
            region_report.update({'Region': region['RegionName']})
            report.append(region_report)
    return report


def get_unattached_volumes(ec2):
    unattached_volumes = {}
    volumes_for_deletion = []
    volumes_for_retention = []
    for volume in ec2.volumes.filter(Filters=[{'Name': 'status', 'Values': ['available']}]):
        logging.info('compiling data for unattached volume %s', volume)
        retain = "false"
        volume_data = {
            'id': volume.id,
            'size': str(volume.size),
            'type': volume.volume_type,
            'iops': str(volume.iops),
            'created': str(volume.create_time),
            'name': "",
        }
        if type(volume.tags) == list:
            for tags in volume.tags:
                if tags["Key"] == 'Retain':
                    retain = tags["Value"]
                elif tags["Key"] == 'Name':
                    volume_name = {'name': tags["Value"]}
                    volume_data.update(volume_name)
        if retain == "false":
            volumes_for_deletion.append(volume_data)
        else:
            volumes_for_retention.append(volume_data)
        logging.info('returning data %s', volume_data)
    if len(volumes_for_retention) > 0:
        unattached_volumes.update({'Retain Volumes': volumes_for_retention})
    if len(volumes_for_deletion) > 0:
        unattached_volumes.update({'Delete Volumes': volumes_for_deletion})
    return unattached_volumes


def get_unscheduled_snapshots(ec2):
    unscheduled_snapshots = {}
    snapshots_for_deletion = []
    snapshots_for_retention = []
    for snapshot in ec2.snapshots.all():
        # filter(Filters=[{'Name': 'description', 'Values': ['This snapshot is created by the AWS Backup service.']}])
        logging.info('compiling data for unscheduled snapshot %s', snapshot)
        retain = "false"
        snapshot_data = {
            'id': snapshot.id,
            # 'size': str(snapshot.size),
            # 'type': snapshot.volume_type,
            # 'iops': str(snapshot.iops),
            # 'created': str(snapshot.create_time),
            # 'name': "",
        }
        if type(snapshot.tags) == list:
            for tags in snapshot.tags:
                if tags["Key"] == 'Retain':
                    retain = tags["Value"]
                elif tags["Key"] == 'Name':
                    snapshot_name = {'name': tags["Value"]}
                    snapshot_data.update(snapshot_name)
        if retain == "false":
            snapshots_for_deletion.append(snapshot_data)
        else:
            snapshots_for_retention.append(snapshot_data)
        logging.info('returning data %s', snapshot_data)
    if len(snapshots_for_retention) > 0:
        unscheduled_snapshots.update(
            {'Retain Volumes': snapshots_for_retention})
    if len(snapshots_for_deletion) > 0:
        unscheduled_snapshots.update(
            {'Delete Volumes': snapshots_for_deletion})
    return unscheduled_snapshots
