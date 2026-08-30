import pytest

from property_campaign.campaign_service import run_campaign
from property_campaign.models import CampaignKind, CampaignRequest, Recipient


@pytest.mark.asyncio
async def test_inspection_campaign_builds_message_and_reports_each_status() -> None:
    sent: list[tuple[str, str, str]] = []

    async def send(to: str, message: str, key: str) -> str:
        sent.append((to, message, key))
        return f"msg-{len(sent)}"

    async def status(message_id: str) -> str:
        return {"msg-1": "delivered", "msg-2": "queued"}[message_id]

    request = CampaignRequest(
        campaign_id="oak-visit-42",
        kind=CampaignKind.inspection_reminder,
        property_name="Oak House",
        recipients=[
            Recipient(phone="+15550000001", tenant_name="Mina", reference="Unit 2, Friday"),
            Recipient(phone="+15550000002", tenant_name="Jon", reference="Unit 7, Monday"),
        ],
    )

    result = await run_campaign(request, send, status)

    assert sent == [
        (
            "+15550000001",
            "Hi Mina, Oak House: inspection Unit 2, Friday is coming up. Please confirm access.",
            "oak-visit-42:0",
        ),
        (
            "+15550000002",
            "Hi Jon, Oak House: inspection Unit 7, Monday is coming up. Please confirm access.",
            "oak-visit-42:1",
        ),
    ]
    assert [item.status for item in result.messages] == ["delivered", "queued"]

