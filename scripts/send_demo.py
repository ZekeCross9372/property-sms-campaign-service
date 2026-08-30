import asyncio
import os

from property_campaign.campaign_service import run_campaign
from property_campaign.infrai_sms import InfraiSmsClient
from property_campaign.models import CampaignKind, CampaignRequest, Recipient


async def main() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    phone = os.environ["DEMO_PHONE"]
    request = CampaignRequest(
        campaign_id="maple-inspection-2026-09",
        kind=CampaignKind.inspection_reminder,
        property_name="Maple Court",
        recipients=[
            Recipient(phone=phone, tenant_name="Alex", reference="Sep 4 at 10:00")
        ],
    )
    async with InfraiSmsClient(api_key) as client:
        result = await run_campaign(request, client.send, client.status)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())

