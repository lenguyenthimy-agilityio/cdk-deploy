from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr as ecr,
    aws_ec2 as ec2,
    Duration,
    CfnOutput,
    SecretValue,
)
from constructs import Construct
from decouple import config as env_config

from configuration import Config


class BackEndStack(Stack):
    """
    BackEnd stack.
    """

    def __init__(
        self, scope: Construct, construct_id: str, props: dict, config: Config, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.namespace = props["namespace"]
        self.output_props = props.copy()
        self.add_webapp(props, config)

    def add_webapp(self, props: dict, config: Config) -> None:
        """Add application stack.
        It will help to start application on ECS Fargate to pull
        and run docker image from ECR.

        Args:
            props (dict): Input properties.
            config (Config): Configuration
        """
        db_instance = props["db_instance"]
        
        role_name = f"ecs-task-role-{self.stack_name}"
        task_role = iam.Role(
            self,
            role_name,
            role_name=role_name,
            assumed_by=iam.ServicePrincipal(service="ecs-tasks.amazonaws.com"),
        )
        
        # ------------------
        # ECS Constructs
        # ------------------
        execution_role_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=["*"],
            actions=[
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
            ],
        )
        # Define task
        task_definition = ecs.FargateTaskDefinition(
            self,
            "ecs-task-definition",
            task_role=task_role,
            cpu=512,
            memory_limit_mib=1024,
        )

        task_definition.add_to_execution_role_policy(execution_role_policy)
        container = task_definition.add_container(
            "web",
            # It will be replaced by the ECR container 
            image=ecs.ContainerImage.from_registry("056575266545.dkr.ecr.us-east-1.amazonaws.com/ecs-devops-repository:latest"),
            logging=ecs.AwsLogDriver(stream_prefix="ecs-logs"),
            environment={
                "ENV": config.env,
                # Database configuration
                "DATABASE_HOST": db_instance.db_instance_endpoint_address,
                "DATABASE_NAME": config.db_name,
                "DATABASE_USER": config.db_username,
                "DATABASE_PASSWORD": config.db_password
            },
        ) 
        container.add_port_mappings(
            ecs.PortMapping(
                container_port=int(config.container_port), protocol=ecs.Protocol.TCP
            )
        )
        
        # vpc = ec2.Vpc(self, "ecs-devops-vpc", max_azs=3)

        cluster = ecs.Cluster(
            self, "ecs-devops-cluster", 
            cluster_name="ecs-devops-cluster", vpc=props["vpc"])
        
        # Create fargate service and ALB
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "ecs-service",
            cluster=cluster,
            task_definition=task_definition,
            service_name="ecs-devops-service",
            public_load_balancer=True,
            desired_count=3,
            listener_port=int(config.listener_port),
            assign_public_ip=True,
        )

        # Config health check.
        fargate_service.target_group.configure_health_check(
            path='/',
            interval=Duration.seconds(120),
            unhealthy_threshold_count=10,
            healthy_threshold_count=5,
        )

        # Config auto scaling
        # scaling = fargate_service.service.auto_scale_task_count(max_capacity=6)
        # scaling.scale_on_cpu_utilization(
        #     "CpuScaling",
        #     target_utilization_percent=10,
        #     scale_in_cooldown=Duration.seconds(amount=60),
        #     scale_out_cooldown=Duration.seconds(amount=60),
        # )

        # self.output_props["fargate_service"] = fargate_service

        # OUTPUT
        # CfnOutput(
        #     self,
        #     "LoadBalancerDNS",
        #     value=fargate_service.load_balancer.load_balancer_dns_name,
        # )
        
    # pass objects to another stack
    @property
    def outputs(self):
        """
        Outputs properties of the stack

        @return: Outputs properties of the stack
        """
        return self.output_props
