#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
import aioboto3
from connectors.source import BaseDataSource


class S3Connector(BaseDataSource):
    """Amazon S3"""

    def __init__(self, definition):
        super().__init__(definition)
        self.session = None

    async def ping(self):
        pass

    async def get_docs(self):
        self.session = aioboto3.Session()
        async with self.session.resource("s3", region_name=self.config["region"]) as s3:
            bucket = await s3.Bucket(self.config["bucket"])
            async for s3_object in bucket.objects.all():
                yield s3_object

    @classmethod
    def get_default_configuration(cls):
        return {
            "bucket": {
                "value": "bucker",
                "label": "AWS Bucket",
                "type": "str",
            },
            "region": {
                "value": "eu-central-1",
                "label": "AWS Region",
                "type": "str",
            },
        }