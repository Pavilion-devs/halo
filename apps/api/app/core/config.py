from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HALO_", env_file=".env", extra="ignore")

    app_name: str = "Halo API"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: str = "sqlite:///./halo.db"
    default_incident_environment: str = "staging"
    default_incident_product: str = "unspecified-product"
    cors_origins: list[str] = ["http://localhost:3000"]
    truefoundry_enabled: bool = False
    truefoundry_base_url: str | None = None
    truefoundry_virtual_account_token: str | None = None
    truefoundry_agent_name_normal: str = "halo-normal"
    truefoundry_agent_name_degraded: str = "halo-degraded"
    truefoundry_agent_name_blackout: str = "halo-blackout"
    truefoundry_agent_id_normal: str | None = None
    truefoundry_agent_id_degraded: str | None = None
    truefoundry_agent_id_blackout: str | None = None
    truefoundry_model_normal: str = "halo/halo-vm-normal"
    truefoundry_model_degraded: str = "halo/halo-vm-degraded"
    truefoundry_model_blackout: str = "halo/halo-vm-degraded"
    truefoundry_mcp_server_observe: str = "jaguar-observe"
    truefoundry_mcp_server_act: str = "jaguar-act"
    truefoundry_request_timeout_seconds: float = 20.0
    truefoundry_guardrails: str | None = None
    truefoundry_user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    truefoundry_agent_versions_path: str = "/api/svc/v1/agent-versions"
    truefoundry_traces_enabled: bool = False
    truefoundry_traces_base_url: str | None = None
    truefoundry_traces_timeout_seconds: float = 10.0
    truefoundry_traces_query_path: str = "/api/svc/v1/spans/query"
    truefoundry_traces_data_routing_destination: str = "default"
    truefoundry_traces_lookback_hours: int = 24
    jaguar_mcp_url: str = "https://www.jaguaralpha.xyz/api/mcp"
    jaguar_mcp_api_key: str | None = None
    jaguar_operator_secret: str | None = None
    jaguar_action_timeout_seconds: float = 20.0


settings = Settings()
