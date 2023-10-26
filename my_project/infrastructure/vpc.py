from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct


class VpcStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, props: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.namespace = props["namespace"]
        self.output_props = {}
        self.add_vpc()

    def add_vpc(self):
        """
        Create a new VPC with no NAT gateway and no private subnet.
        """

        # cidr = "10.0.0.0/16"
        # vpc = ec2.Vpc(
        #     self,
        #     f"{self.namespace}-VPC",
        #     nat_gateways=0,
        #     subnet_configuration=[
        #         ec2.SubnetConfiguration(
        #             name="public-subnet", subnet_type=ec2.SubnetType.PUBLIC
        #         )
        #     ],
        # )
        vpc = ec2.Vpc(self, "ecs-devops-vpc", max_azs=3)

        self.output_props = {"vpc": vpc}

    # pass objects to another stack
    @property
    def outputs(self):
        return self.output_props
