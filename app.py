import os
import re
from fastapi import FastAPI, Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

app = FastAPI()
handler = SlackRequestHandler(slack_app)

@app.post("/slack/events")
async def slack_events(req: Request):
    return await handler.handle(req)

def convert_to_slack_markdown(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'^\s*#+\s+(.*)$', r'*\1*', text, flags=re.MULTILINE) # heading
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<\2|\1>', text) # link [hi](https://url)
    text = re.sub(r'~~(.*?)~~', r'~\1~', text) # strikethrough
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text) # bold
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'_\1_', text) # italics
    text = re.sub(r'^\s*[\*\-]\s+', r'• ', text, flags=re.MULTILINE) # bullet points
    text = re.sub(r'^\s*>\s?(.*)$', r'> \1', text, flags=re.MULTILINE) #quote
    
    return text

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
                    },
                    {
                        "type": "input",
                        "block_id": "daily_picture",
                        "optional": True,
                        "label": {
                            "type": "plain_text",
                            "text": "attach pictures"
                        },
                        "element": {
                            "type": "file_input",
                            "action_id": "picture"
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
    raw_details = state["daily_details"]["details"]["value"]
    details = convert_to_slack_markdown(raw_details)
    picture_block = state.get("daily_picture", {}).get("picture", {})
    picture_files = picture_block.get("files", [])
    
    group_id = os.environ.get("PINGLISHA_GROUP_ID", "")
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
            "alt_text": picture.get("name", "attached picture")
        })

    try:
        client.chat_postMessage(
            channel=channel_id,
            text="my daily recap",
            blocks=blocks
        )
    except Exception as e:
        print(f"ERROR POSTING MESSAGE: {e}")