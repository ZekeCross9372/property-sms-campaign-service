import os

from fastapi import FastAPI, HTTPException

from .campaign_service import run_campaign
from .infrai_sms import InfraiError, InfraiSmsClient
from .models import CampaignRequest, CampaignResult

app = FastAPI(title="Property campaign SMS service")


@app.post("/campaigns", response_model=CampaignResult)
async def create_campaign(request: CampaignRequest) -> CampaignResult:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    try:
        async with InfraiSmsClient(api_key) as client:
            return await run_campaign(request, client.send, client.status)
    except InfraiError as error:
        client_status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": error.code, "error": error.detail},
        ) from error

