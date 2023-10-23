from aws_cdk import (
    Stack,
    aws_s3 as s3,
    RemovalPolicy,
)
from constructs import Construct

from configuration import Config


class S3Stack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props: dict, config, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.namespace = props["namespace"]
        self.output_props = props.copy()
        self.add_s3(config)

    def add_s3(self, config: Config) -> None:
        artifact_bucket = s3.Bucket(
            self,
            "ArtifactBucket",
            bucket_name="lenguyen-bucket-demo",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.KMS_MANAGED,
        )

        self.output_props["artifact_bucket"] = artifact_bucket

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props
