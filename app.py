#!/usr/bin/env python3
import os

import aws_cdk as cdk

from my_project.infrastructure.s3 import S3Stack
from my_project.infrastructure.backend import BackEndStack
from my_project.infrastructure.cicd import BackendCICDStack
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

# Create Backend Stack
output_props = {**props}
application_stack = BackEndStack(
    app, f"{namespace}-BackEndStack", output_props, config, env=env
)

# Create Backend CI/CD
output_props = {**props, **s3_stack.output_props, **application_stack.output_props}
backend_cicd_stack = BackendCICDStack(
    app, f"{namespace}-BackendCICDStack", output_props, config, env=env
)

app.synth()
