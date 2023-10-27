#!/usr/bin/env python3
import os

import aws_cdk as cdk

from my_project.infrastructure.s3 import S3Stack
from my_project.infrastructure.backend import BackEndStack
from my_project.infrastructure.vpc import VpcStack
from my_project.infrastructure.storage import StorageStack
from configuration import get_config


app = cdk.App()
config = get_config()

# Config environment
env = cdk.Environment(account=config.aws_account_id, region=config.aws_region)

print("***ENV***", env)
namespace = f"{config.namespace}-{config.env}"
props = {"namespace": namespace}

# Create VPC
vpc_stack = VpcStack(app, f"{namespace}-VpcStack", props, env=env)

# Restore RDS from snapshot
output_props = {**props, **vpc_stack.outputs}
storage_stack = StorageStack(
    app, f"{namespace}-StorageStack", output_props, config, env=env
)

# Create S3 buckets
output_props = {**props}
s3_stack = S3Stack(app, f"{namespace}-S3Stack", output_props, config, env=env)

# Create Backend Stack
output_props = {**props, **vpc_stack.outputs, **storage_stack.outputs}
application_stack = BackEndStack(
    app, f"{namespace}-BackEndStack", output_props, config, env=env
)

app.synth()
