import os
import json

import boto3

from bikefinder.util import database


@database
def bikes_from_db_to_s3(event, context):
    for provider in ['JUMP', 'limebike', 'spin', 'mobike', 'ofo']:
        data = [(r.location.y, r.location.x, r.count) for r in context.db.query(
            """
            select location, count(*) from bike_locations
            where provider=:provider and created > (now()-'5day'::interval)
            group by location
            """,
            provider=provider,
        )]
        boto3.client('s3').put_object(
            Body=json.dumps(data),
            Bucket='bikehero-labs-dobi-heatmaps',
            Key=f"{provider}.json",
            ACL='public-read',
        )
