from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    asr_provider: str = Field(default="mock", alias="asrProvider")
    diarization_provider: str = Field(default="mock", alias="diarizationProvider")
    llm_provider: str = Field(default="mock", alias="llmProvider")
    llm_base_url: str = Field(default="", alias="llmBaseUrl")
    llm_model: str = Field(default="mock", alias="llmModel")
    cloud_llm_enabled: bool = Field(default=False, alias="cloudLlmEnabled")
    store_transcript: bool = Field(default=True, alias="storeTranscript")
    debug_log_transcript: bool = Field(default=False, alias="debugLogTranscript")
    data_dir: str = Field(default="", alias="dataDir")
    api_key_configured: bool = Field(default=False, alias="apiKeyConfigured")

    model_config = {"populate_by_name": True}
