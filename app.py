import os
import json
from fastapi import FastAPI, Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from web import router as web_router

slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    token_verification_enabled=False,
    process_before_response=True,
)

app = FastAPI()
handler = SlackRequestHandler(slack_app)

app.include_router(web_router)

def trigger_modal(client, trigger_id, channel_id, thread_ts=None):
    metadata = json.dumps({
        "channel_id": channel_id,
        "thread_ts": thread_ts
    })

    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "lisha_daily_modal",
            "private_metadata": metadata,
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


# @slack_app.command("/lisha-daily")
# def handle_slash_command(ack, body, client):
#     ack()
#     try:
#         trigger_modal(
#             client=client,
#             trigger_id=body["trigger_id"],
#             channel_id=body["channel_id"]
#         )
#     except Exception as e:
#         print(f"ERROR OPENING MODAL: {e}")

@slack_app.action("open_lisha_modal")
def handle_button_click(ack, body, client):
    ack()
    
    clicker_user_id = body["user"]["id"]
    allowed_user_id = os.environ.get("ALISHA_SLACK_USER_ID")

    if clicker_user_id != allowed_user_id:
        try:
            channel_id = body["channel"]["id"]
            thread_ts = body["message"].get("thread_ts") or body["message"]["ts"]
            client.chat_postEphemeral(
                channel=channel_id,
                user=clicker_user_id,
                thread_ts=thread_ts,
                text="YOU ARE NOT ALISHA GRR"
            )
        except Exception as e:
            print(f"ERROR SENDING EPHEMERAL MSG: {e}")
        return
    try:
        channel_id = body["channel"]["id"]
        thread_ts = body["message"].get("thread_ts") or body["message"]["ts"]

        trigger_modal(
            client=client,
            trigger_id=body["trigger_id"],
            channel_id=channel_id,
            thread_ts=thread_ts
        )
    except Exception as e:
        print(f"ERROR OPENING MODAL FROM BUTTON: {e}")


@app.get("/api/cron-checkpoint")
@app.post("/api/cron-checkpoint")
async def cron_checkpoint():
    try:
        user_id = os.environ.get("ALISHA_SLACK_USER_ID")
        channel_id = os.environ.get("SLACK_CHANNEL_ID") 
        parent_msg = slack_app.client.chat_postMessage(
            channel=channel_id,
            text=f"helloo <@{user_id}>! how was your dayy? :3"
        )
        parent_ts = parent_msg["ts"]

        slack_app.client.chat_postMessage(
            channel=channel_id,
            thread_ts=parent_ts,
            text="click below to share your daily update!",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "click below to share your daily update:"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "share daily update"
                            },
                            "action_id": "open_lisha_modal"
                        }
                    ]
                }
            ]
        )
        return {"status": "success"}
    except Exception as e:
        print(f"ERROR IN CRON CHECKPOINT: {e}")
        return {"status": "error", "message": str(e)}
    
@slack_app.view("lisha_daily_modal")
def submit_daily_update(ack, view, client):
    ack()

    metadata = json.loads(view["private_metadata"])
    channel_id = metadata["channel_id"]
    thread_ts = metadata.get("thread_ts")

    state = view["state"]["values"]
    raw_details = state["daily_details"]["details"]["value"]
    details = raw_details

    picture_block = state.get("daily_picture", {}).get("picture", {})
    picture_files = picture_block.get("files", [])

    group_id = os.environ.get("PINGLISHA_GROUP_ID", "")

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    # f"hi hello <!subteam^{group_id}>!\n"
                    # "here is what lisha has to say today:"
                    f"hi hello! here is what lisha has to say today:"
                )
            }
        },
        {
            "type": "markdown",
            "text": details
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

    main_text = f"hi <!subteam^{group_id}>! here is what lisha has to say today!\n\n{details}"

    post_kwargs = {
        "channel": channel_id,
        "text": main_text,
        "blocks": blocks
    }
    
    if thread_ts:
        post_kwargs["thread_ts"] = thread_ts
        post_kwargs["reply_broadcast"] = True

    try:
        client.chat_postMessage(**post_kwargs)

        client.chat_postMessage(
            channel=channel_id,
            text=":threadparrot:"
        )

        if thread_ts:
            try:
                client.reactions_add(
                    channel=channel_id,
                    name="tickalisha",
                    timestamp=thread_ts
                )
            except Exception as rx_err:
                print(f"ERROR ADDING REACTION: {rx_err}")

    except Exception as e:
        print(f"ERROR POSTING DAILY UPDATE: {e}")

@app.post("/slack/events")
async def slack_events(req: Request):
    return await handler.handle(req)