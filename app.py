import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])

@app.command("/lisha-daily")
def open_daily_modal(ack, body, client):
    ack()

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
                        "text": "share a picture (optional)"
                    },
                    "element": {
                        "type": "file_input",
                        "action_id": "picture",
                        "filetypes": ["png", "jpg", "jpeg", "gif"],
                        "max_files": 1
                    }
                }
            ]
        }
    )


@app.view("lisha_daily_modal")
def submit_daily_update(ack, body, view, client):
    ack()

    state = view["state"]["values"]
    details = state["daily_details"]["details"]["value"]
    picture_files = state["daily_picture"]["picture"].get("files", [])
    group_id = os.environ["PINGLISHA_GROUP_ID"]
    channel_id = view["private_metadata"]
    blocks = [
        {
            "type": "markdown",
            "text": f"hi <!subteam^{group_id}>! here is what lisha has to say today! how was your day? :D\n\n{details}"
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


if __name__ == "__main__":
    SocketModeHandler(
        app,
        os.environ["SLACK_APP_TOKEN"]
    ).start()