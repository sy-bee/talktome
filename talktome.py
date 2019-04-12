#/usr/bin/env python
import glob
import json
import logging
import os

import yaml

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, make_response
from slackeventsapi import SlackEventAdapter

from lib import core, zendesk, messaging

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)

SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]

# scheduler
scheduler = BackgroundScheduler()
# find all workflows and build a TalkCore for each of them.
talk_core = {}
for config in glob.glob("configs/*.yaml"):
    workflow = yaml.safe_load(file(config))
    talk_core[workflow['label']] = core.TalkCore(
        os.environ["SLACK_BOT_TOKEN"],
        "dropbox.com",
        os.environ["ZENDESK_URL"],
        os.environ["ZENDESK_EMAIL"],
        os.environ["ZENDESK_API"],
        workflow,
    )
    scheduler.add_job(talk_core[workflow['label']].run, 'interval', minutes=1)

scheduler.start()

# Helper for verifying that requests came from Slack
def verify_slack_token(request_token):
    if SLACK_VERIFICATION_TOKEN != request_token:
        logging.error("Error: invalid verification token!")
        logging.error("Received %s but was expecting %s", request_token, SLACK_VERIFICATION_TOKEN)
        return make_response("Request contains invalid Slack verification token", 403)

@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    # Parse the request payload
    json_data = json.loads(request.form["payload"])
    # Verify that the request came from Slack
    verify_slack_token(json_data["token"])
    # Route to correct TalkCore
    for block in json_data['message']['blocks']:
        if block['block_id'] in talk_core:
            talk_core[block['block_id']].message_actions(json_data)
    return make_response("", 200)

# Create an event listener for "reaction_added" events and print the emoji name
@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    emoji = event_data["event"]["reaction"]
    channel = event_data["event"]["item"]["channel"]
    slack_client.api_call("chat.postMessage", channel=channel, text="Cheers for :{}:".format(emoji))

@slack_events_adapter.on("message")
def app_home(event_data):
    verify_slack_token(event_data["token"])
    if not "text" in event_data["event"]:
        return
    text = event_data["event"]["text"]
    channel = event_data["event"]["channel"]
    if "joke" in text:
        slack_client.api_call("chat.postMessage", channel=channel,
            text="He was so narrow-minded he could see through a keyhole with both eyes.")

@app.route("/")
def hello():
    return "Go away!"

# Start the server on port 3000
if __name__ == "__main__":
    app.run(port=3000)
