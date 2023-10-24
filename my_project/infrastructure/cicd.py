from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    SecretValue,
    RemovalPolicy
)

from constructs import Construct

from configuration import Config


class BackendCICDStack(Stack):
    
    def __init__(
        self, scope: Construct, construct_id: str, props: dict, config: Config, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.namespace = props["namespace"]
        self.output_props = props.copy()
        self.add_cicd(props, config)
        
    def add_cicd(self, props: dict, config: Config):
        """Add CI CD Stack

        Args:
            props (dict): properties from other stack.
            config (Config): Configuration
        """
        
        fargate_service = props["fargate_service"]
        github_repo_name = config.github_repo_name
        github_owner = config.github_owner
        git_branch = config.git_branch
        secrets_manager_github_token = config.secrets_manager_github_token
        
        # ECR repository
        ecr_repository = ecr.Repository(
            self,
            "ecr_repo",
            repository_name="lenguyen",
            removal_policy=RemovalPolicy.DESTROY,
        )

        github_source = codebuild.Source.git_hub(
            owner=github_owner,
            repo=github_repo_name,
            webhook=False,
        )
        
        # CodeBuild project
        codebuild_project = codebuild.Project(
            self,
            "CodeBuildProject",
            project_name=self.stack_name,
            source=github_source,
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_2,
                privileged=True,
            ),
            environment_variables={
                "ECR_REPO_URI": codebuild.BuildEnvironmentVariable(
                    value=ecr_repository.repository_uri
                ),
                "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value=config.env),
            },
            build_spec=codebuild.BuildSpec.from_object(
                {
                    "version": "0.2",
                    "phases": {
                        "pre_build": {
                            "commands": [
                                "env",
                                "export TAG=${CODEBUILD_RESOLVED_SOURCE_VERSION}",
                            ]
                        },
                        "build": {
                            "commands": [
                                "docker build -t $ECR_REPO_URI:$TAG ./",
                                "docker tag $ECR_REPO_URI:$TAG $ECR_REPO_URI:$ENVIRONMENT",
                                "$(aws ecr get-login --no-include-email)",
                                "echo $ECR_REPO_URI:$TAG",
                                "docker push $ECR_REPO_URI:$TAG",
                                "docker push $ECR_REPO_URI:$ENVIRONMENT",
                            ]
                        },
                        "post_build": {
                            "commands": [
                                'echo "In Post-Build Stage"',
                                'printf \'[{"name":"web","imageUri":"%s"}]\' $ECR_REPO_URI:$TAG > imagedefinitions.json',
                                "pwd; ls -al; cat imagedefinitions.json",
                            ]
                        },
                    },
                    "artifacts": {"files": ["imagedefinitions.json"]},
                }
            ),
            # Enable Docker caching
            cache=codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
        )
        # Pipeline Actions
        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact()

        source_action = codepipeline_actions.GitHubSourceAction(
            action_name="Github_Source",
            owner=github_owner,
            repo=github_repo_name,
            branch=git_branch,
            oauth_token=SecretValue.secrets_manager(secrets_manager_github_token),
            output=source_output,
        )

        build_action = codepipeline_actions.CodeBuildAction(
            action_name="CodeBuild",
            project=codebuild_project,
            input=source_output,
            outputs=[build_output],
        )

        deploy_action = codepipeline_actions.EcsDeployAction(
            action_name="DeployAction",
            service=fargate_service.service,
            image_file=codepipeline.ArtifactPath(build_output, "imagedefinitions.json"),
        )

        # Pipeline Stages
        codepipeline.Pipeline(
            self,
            f"{self.namespace}-BEPipeline",
            artifact_bucket=props["artifact_bucket"],
            stages=[
                codepipeline.StageProps(stage_name="Source", actions=[source_action]),
                codepipeline.StageProps(stage_name="Build", actions=[build_action]),
                codepipeline.StageProps(
                    stage_name="Deploy-to-ECS", actions=[deploy_action]
                ),
            ],
        )

        ecr_repository.grant_pull_push(codebuild_project.role)
        codebuild_project.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ecs:DescribeCluster",
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                ],
                resources=[fargate_service.cluster.cluster_arn],
            )
        )
        self.output_props["ecr_repository"] = ecr_repository

    # pass objects to another stack
    @property
    def outputs(self):
        """
        Outputs of the stack
        @return: output properties
        """
        return self.output_props