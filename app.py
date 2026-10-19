import os
from fastapi import FastAPI, Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.web.internal_utils import _get_custom_headers

slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

app = FastAPI()
handler = SlackRequestHandler(slack_app)

@app.post("/slack/events")
async def slack_events(req: Request):
    return await handler.handle(req)

@slack_app.command("/lisha-daily")
def open_daily_modal(ack, body, client):
    ack()
    try:
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "lisha_daily_modal",
                "private_metadata": body["channel_id"],
                "title": {
                    "type": "plain_text",
                    "text": "today's recap:"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "send update"
                },
                "close": {
                    "type": "plain_text",
                    "text": "cancel"
                },
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "daily_details",
                        "label": {
                            "type": "plain_text",
                            "text": "what happened today?"
                        },
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "details",
                            "multiline": True,
                            "placeholder": {
                                "type": "plain_text",
                                "text": "markdown is supported!"
                            }
                        }
                    }
                ]
            }
        )
    except Exception as e:
        print(f"ERROR OPENING MODAL: {e}")

@slack_app.view("lisha_daily_modal")
def submit_daily_update(ack, view, client):
    ack()

    state = view["state"]["values"]
    details = state["daily_details"]["details"]["value"]
    picture_files = state["daily_picture"]["picture"].get("files", [])
    group_id = os.environ["PINGLISHA_GROUP_ID"]
    channel_id = view["private_metadata"]
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"hi <!subteam^{group_id}>! here is what lisha has to say today!\n\n{details}"
            }
        }
    ]

    for picture in picture_files:
        blocks.append({
            "type": "image",
            "slack_file": {
                "id": picture["id"]
            },
            "alt_text": picture.get("name", "some picture")
        })

    client.chat_postMessage(
        channel=channel_id,
        text="my daily recap",
        blocks=blocks
    )

app = FastAPI()
handler = SlackRequestHandler(slack_app)

@app.post("/slack/events")
async def endpoint(req: Request):
    return await handler.handle(req)