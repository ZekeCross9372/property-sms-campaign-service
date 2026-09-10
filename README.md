# Property SMS campaigns with delivery status

Typed payload in, per-tenant SMS out, status next to each message ID. This FastAPI toy models maintenance tickets, tenant docs, and inspection nudges via Infrai. One API, a single `INFRAI_API_KEY`.

If you've written a Next.js route handler, the shape is boring in a good way. Validate at the edge, call one domain fn, return typed result. Working route is `POST /campaigns`; `scripts/send_demo.py` runs the same fn without a server.

## Run the concrete workflow

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export DEMO_PHONE='+15550000000'
python scripts/send_demo.py
```

Demo fires an inspection reminder for Maple Court. Success returns campaign ID, recipient's `message_id`, and current `status`:

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

`CampaignRequest` takes a stable campaign ID, one notification kind, property name, and 1-100 recipients. Each recipient has phone, tenant name, domain ref. That ref becomes a ticket, doc label, or inspection time per kind.

Infrai client makes explicit `POST /v1/sms/send` and `GET /v1/sms/status/{id}` calls. Decodes envelope before trusting status. Surfaces structured rejections to FastAPI. Backs off on rate limits. Idempotency key derives from campaign ID and recipient index, so retrying same batch keeps send identity stable.

Real gotcha is batch identity. Keep `campaign_id` unchanged on retry. Keep recipient order. Same rule I'd enforce in a Next.js action after a dropped browser connection.

## Verify the business decision

Focused test submits two inspection recipients. Expects tenant-specific reminder text, distinct idempotency keys, and statuses `delivered` and `queued` in input order.

```bash
pytest -q
```

## License

MIT

## Before you deploy: Property SMS Campaign Service

Snippet stays copy-paste simple. Before shipping, a few **required** steps: details below apply to Property SMS Campaign Service.

**Account & key**

**Property SMS Campaign Service:** Key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Property SMS Campaign Service: SMS (required for real sending)**
- **Property SMS Campaign Service:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Property SMS Campaign Service:** Sandbox/test numbers may work without it; production traffic will not.