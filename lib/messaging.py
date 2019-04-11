#/usr/bin/env python
import datetime
import logging
import time

import requests
import yaml

from slackclient import SlackClient


class SlackWorker(object):
    """
    Iterates over tickets, creates/opens conversations
    """
    def __init__(self, bot_token, verification_token, domain):
        self.client = SlackClient(bot_token)
        self.verification_token = verification_token
        self.domain = domain
        # TODO: change this
        self.bot_name = "Talktome"
        # TODO abstract away workflows and connect them with the search params
        self.workflow = yaml.load(file("lib/messages.yaml"))

    def process_tickets(self, tickets):
        """
        Iterate over tickets and engage with users
        """
        for ticket_id, ticket_data in tickets.items():
            slack_user = self.get_slack_user(ticket_data.username)
            # check if there was a conversation with the user regarding this ticket
            conversation = self.client.api_call("conversations.open", users=[slack_user])
            channel_id = conversation['channel']['id']
            # TODO: change to 30 days
            month_ago = datetime.datetime.now() - datetime.timedelta(minutes=2)
            timestamp = time.mktime(month_ago.timetuple())
            history = self.client.api_call("conversations.history", channel=channel_id,
                                           oldest=timestamp)
            # search for a last message sent by bot
            last_message = {}
            for message in history['messages']:
                if 'bot_id' in message and message['username'] == self.bot_name:
                    last_message = message
                    break
            # first time message
            if not last_message:
                text = self.workflow['message'].format(barcode=ticket_data.barcode)
                choices = self.workflow['choices']
                blocks = self.build_blocks(text, choices, ticket_id)
                logging.debug(blocks)
                self.send_block_message(channel_id, blocks)
            # nudge a user if last message is an unanswered question
            else:
                # TODO
                pass


    def generate_response(self, json_data):
        """
        Generates a response for an action performed by a user, e.g. button click.
        Returns a dict with ticket id and a message if a ticket needs to ne updated.
        """
        # delete all actions
        logging.debug("incoming %s", json_data)
        no_button_blocks = [
            block for block in json_data['message']['blocks'] if block['type'] != "actions"]
        #requests.post(json_data["response_url"], json={'blocks': json_data['blocks'],
        #    "token": json_data["token"], "channel": json_data["channel"]["id"],
        #    "replace_original": True}, headers={'Content-Type': 'application/json'})
        # find and send next response. We are taking first action, rest are ignored
        actions = json_data['actions'][0]
        ticket_id = actions['value']
        action_id = actions['action_id']
        channel_id = json_data['container']['channel_id']
        message_ts = json_data['container']['message_ts']
        self.client.api_call("chat.update", channel=channel_id, ts=message_ts,
                             blocks=no_button_blocks)
        current_step = self.recurse_workflow(self.workflow, action_id)
        update_ticket = {}
        if "choices" in current_step:
            blocks = self.build_blocks(current_step['message'], current_step['choices'],
                                                   ticket_id)
            self.send_block_message(channel_id, blocks)
        elif "update_ticket" in current_step:
            update_ticket[ticket_id] = current_step["update_ticket"]
            self.send_text_message(channel_id, current_step['message'])
        return update_ticket

    def recurse_workflow(self, step, key):
        """
        Recurses and returns requested workflow step
        """
        if not isinstance(step, dict):
            return step
        if "choices" in step.keys():
            if key in step["choices"].keys():
                return step["choices"][key]
            else:
                for choice in step["choices"].keys():
                    result = self.recurse_workflow(step["choices"][choice], key)
                    if result:
                        return result

    def create_button(self, label, action, ticket_id):
        """
        Generates necessary structure for a button.
        """
        return {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": label,
            },
            "value": str(ticket_id),
            "action_id": str(action)
        }

    def build_blocks(self, text, choices, ticket_id):
        return [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": text,
                }
            },
            {
                "type": "actions",
                "elements": [self.create_button(data['label'], action, ticket_id)
                             for action, data in choices.items()]
            },
        ]

    def get_slack_user(self, username):
        """
        Returns slack user id based on username
        """
        return self.client.api_call("users.lookupByEmail",
            email="{}@{}".format(username, self.domain))['user']['id']

    def send_text_message(self, channel_id, text):
        """
        Sends a basic text message to a given channel.
        """
        self.client.api_call("chat.postMessage", channel=channel_id, text=text)

    def send_block_message(self, channel_id, blocks):
        """
        Sends given list of blocks to a channel with id.
        """
        self.client.api_call("chat.postMessage", channel=channel_id, blocks=blocks)
