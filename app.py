#!/usr/bin/env python3
import os

import aws_cdk as cdk

from my_project.infrastructure.s3 import S3Stack
from configuration import get_config


app = cdk.App()
config = get_config()

# Config environment
env = cdk.Environment(account=config.aws_account_id, region=config.aws_region)

print("***ENV***", env)
namespace = f"{config.namespace}-{config.env}"
props = {"namespace": namespace}

# Create S3 buckets
output_props = {**props}
s3_stack = S3Stack(app, f"{namespace}-S3Stack", output_props, config, env=env)

app.synth()
