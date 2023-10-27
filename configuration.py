"""Module for configuration management"""
import configparser
import dataclasses
import os
from decouple import config


@dataclasses.dataclass
class Config:
    """
    Represents the configuration options for this app
    """

    namespace: str

    # AWS configuration
    aws_region: str
    aws_account_id: str
    # aws_access_key_id: str
    # aws_secret_access_key: str

    # Backend GitHub configuration
    github_repo_name: str
    github_owner: str
    git_branch: str
    secrets_manager_github_token: str

    # Application configuration
    container_port: int
    listener_port: int
    health_check_path: str
    env: str

    # -------------------------------------------------------------------------
    # ECR configuration
    # -------------------------------------------------------------------------
    ecr_repo_name: str

    # Health check secure token
    # health_check_secure_token: str

    # Database settings
    db_name: str
    db_username: str
    db_password: str
    db_port: int
    

def get_config() -> Config:
    """
    Returns the configuration for the app based on the environment

    @return: The configuration for the app
    """
    env = config("environment", "")
    print("=====================================================================")
    print(f"====================== ENV: {env} ===================================")
    print("=====================================================================")

    configuration_file = f"configuration-{env}.ini"

    path_to_config_file = os.path.join(os.path.dirname(__file__), configuration_file)
    if not os.path.isfile(path_to_config_file):
        raise ValueError(f"Invalid environment: {env}")

    cfg = configparser.ConfigParser()
    cfg.read(path_to_config_file)

    return Config(**cfg["main"])
