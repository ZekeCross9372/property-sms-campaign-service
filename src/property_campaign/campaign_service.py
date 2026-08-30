from collections.abc import Awaitable, Callable

from .models import CampaignKind, CampaignRequest, CampaignResult, MessageResult, Recipient


Send = Callable[[str, str, str], Awaitable[str]]
Status = Callable[[str], Awaitable[str]]


def message_for(kind: CampaignKind, property_name: str, recipient: Recipient) -> str:
    opening = f"Hi {recipient.tenant_name}, {property_name}:"
    if kind is CampaignKind.maintenance_request:
        return f"{opening} maintenance request {recipient.reference} has been scheduled."
    if kind is CampaignKind.tenant_document:
        return f"{opening} tenant document {recipient.reference} is ready for review."
    return f"{opening} inspection {recipient.reference} is coming up. Please confirm access."


async def run_campaign(
    request: CampaignRequest,
    send: Send,
    status: Status,
) -> CampaignResult:
    results: list[MessageResult] = []
    for index, recipient in enumerate(request.recipients):
        message_id = await send(
            recipient.phone,
            message_for(request.kind, request.property_name, recipient),
            f"{request.campaign_id}:{index}",
        )
        delivery_status = await status(message_id)
        results.append(
            MessageResult(
                phone=recipient.phone,
                message_id=message_id,
                status=delivery_status,
            )
        )
    return CampaignResult(campaign_id=request.campaign_id, messages=results)

