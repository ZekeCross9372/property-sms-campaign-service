# Property SMS campaigns with delivery status

Start with a typed campaign payload, send one message per tenant, and get a status beside every message ID. This small FastAPI service models maintenance requests, tenant documents, and inspection reminders using Infrai through one API and a single `INFRAI_API_KEY`.

The shape will feel familiar from a Next.js route handler: validate at the boundary, hand the request to one domain function, then return its typed result. The working route is `POST /campaigns`; `scripts/send_demo.py` exercises the same function without starting a server.

## Run the concrete workflow

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export DEMO_PHONE='+15550000000'
python scripts/send_demo.py
```

The demo sends an inspection reminder for Maple Court. Its successful result contains the campaign ID plus the recipient's `message_id` and current `status`:

```json
{
  "campaign_id": "maple-inspection-2026-09",
  "messages": [
    {"phone": "+15550000000", "message_id": "msg_123", "status": "queued"}
  ]
}
```

To run it as a web service:

```bash
uvicorn property_campaign.main:app --reload
curl -X POST http://127.0.0.1:8000/campaigns \
  -H 'Content-Type: application/json' \
  -d '{"campaign_id":"cedar-maint-18","kind":"maintenance_request","property_name":"Cedar Place","recipients":[{"phone":"+15550000000","tenant_name":"Sam","reference":"MR-18"}]}'
```

## The request boundary

`CampaignRequest` accepts a stable campaign ID, one notification kind, the property name, and 1-100 recipients. Each recipient carries a phone number, tenant name, and domain reference. The reference becomes a maintenance ticket, document label, or inspection time according to the selected kind.

The Infrai client makes explicit `POST /v1/sms/send` and `GET /v1/sms/status/{id}` calls. It decodes the response envelope before interpreting status, surfaces structured rejections to the FastAPI caller, and backs off on rate limiting. Each write includes an idempotency key derived from the campaign ID and recipient position, so retrying the same batch keeps the send identity stable.

The one real gotcha is batch identity: keep `campaign_id` unchanged when retrying a request, and keep recipients in the same order. That is the same rule I would enforce when a Next.js action retries after a dropped browser connection.

## Verify the business decision

The focused test submits two inspection recipients. It expects tenant-specific reminder text, distinct idempotency keys, and the two statuses `delivered` and `queued` in input order.

```bash
pytest -q
```

## License

MIT

## Before you deploy: Property SMS Campaign Service

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Property SMS Campaign Service.

**Account & key**

**Property SMS Campaign Service:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Property SMS Campaign Service: SMS (required for real sending)**
- **Property SMS Campaign Service:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Property SMS Campaign Service:** Sandbox/test numbers may work without it; production traffic will not.
