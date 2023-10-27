"""
This is storage stack. It creates RDS instance or restores from snapshot.
"""

from typing import Dict

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
)
from constructs import Construct

from configuration import Config


class StorageStack(Stack):
    """
    Storage stack. It creates an RDS instance.
    """

    def __init__(
        self, scope: Construct, construct_id: str, props: Dict, config: Config, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.namespace = props["namespace"]
        self.output_props = props.copy()
        self.add_rds(props, config)

    @classmethod
    def get_db_engine(cls):
        """
        Get database engine

        :param engine: Database engine name.
        :return: RDS Database Engine
        """
      
        return rds.DatabaseInstanceEngine.postgres(
            version=rds.PostgresEngineVersion.of("12", "12.7")
        )

    def add_rds(self, props: dict, config: Config) -> None:
        """
        Add new RDS instance or restore from snapshot.

        :param props: properties from other stack.
        :param config: Configuration
        """
        vpc = props["vpc"]
        db_port = int(config.db_port)
        engine = self.get_db_engine()

        db_security_groups = ec2.SecurityGroup(
            self, f"{self.namespace}-DBSecurityGroup", vpc=vpc
        )

        db_security_groups.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(db_port))
        
        properties = {
            "engine": engine,
            # optional, defaults to m5.large
            "instance_type": ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.SMALL
            ),
            "vpc": vpc,
            "vpc_subnets": {"subnet_type": ec2.SubnetType.PUBLIC},
            "allocated_storage": 20,  # 20GiB
            "max_allocated_storage": 30,  # 30 GiB
            "multi_az": False,
            "port": db_port,
            "security_groups": [db_security_groups],
        }
       
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstance.html
        # Add new RDS instance
        db_instance = rds.DatabaseInstance(
            self,
            f"{self.namespace}-DBInstance",
            database_name=config.db_name,
            credentials=rds.Credentials.from_generated_secret(config.db_username),
            storage_encrypted=True,
            **properties,
        )

        self.output_props["db_instance"] = db_instance

    # pass objects to another stack
    @property
    def outputs(self) -> Dict:
        """
        Outputs properties
        @return: Outputs properties
        """
        return self.output_props