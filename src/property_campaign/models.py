from enum import Enum

from pydantic import BaseModel, Field


class CampaignKind(str, Enum):
    maintenance_request = "maintenance_request"
    tenant_document = "tenant_document"
    inspection_reminder = "inspection_reminder"


class Recipient(BaseModel):
    phone: str = Field(min_length=7)
    tenant_name: str = Field(min_length=1)
    reference: str = Field(min_length=1)


class CampaignRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    kind: CampaignKind
    property_name: str = Field(min_length=1)
    recipients: list[Recipient] = Field(min_length=1, max_length=100)


class MessageResult(BaseModel):
    phone: str
    message_id: str
    status: str


class CampaignResult(BaseModel):
    campaign_id: str
    messages: list[MessageResult]

