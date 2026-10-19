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
                "text": "here's my today's recap :yay:"
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
                            "text": "projects, progress, side quests, anything..."
                        }
                    }
                }
            ]
        }
    )

@app.view("lisha_daily_modal")
def submit_daily_update(ack, body, view, client):
    ack()

    details = (
        view["state"]["values"]
        ["daily_details"]["details"]["value"]
    )

    group_id = os.environ["PINGLISHA_GROUP_ID"]

    client.chat_postMessage(
        channel=view["private_metadata"],
        text=f"<!subteam^{group_id}> *lisha's daily recap*\n{details}"
    )


if __name__ == "__main__":
    SocketModeHandler(
        app,
        os.environ["SLACK_APP_TOKEN"]
    ).start()
