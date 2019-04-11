#/usr/bin/env python
import logging
import re

from zdesk import Zendesk

SEARCH_STRING = 'tags:corpeng_primary_remediation out of date status:open status:new group:support'
TALKTOME_AUTHOR = 'talktome'


class TicketData(object):
    """
    Response containing necessary ticket data.
    """
    def __init__(self, username, machine_barcode, ticket_status):
        self.username = username
        self.barcode = machine_barcode
        self.status = ticket_status


class ZenWorker(object):
    def __init__(self, url, email, api):
        self.zendesk = Zendesk(url, zdesk_email=email, zdesk_api=api)
        self.barcode_re = re.compile(r"barcode\s(\d+)")
        self.username_re = re.compile(r"assigned_to\s(\w+)")

    def run(self):
        """
        Iterates through the tickets found by SEARCH_STRING and
        """
        try:
            result = self.zendesk.search(query=SEARCH_STRING, get_all_pages=True)
        except Exception as exc:
            logging.error("encountered an exception during a zendesk search: %s", str(exc))
            return
        logging.debug("found %s tickets in the queue", str(result['count']))
        tickets = {}
        # iterating over the tickets which haven't been touched
        for ticket in result['results']:
            try:
                comments = self.zendesk.ticket_comments(ticket_id=ticket['id'])
            except Exception as exc:
                logging.error("encountered an error %s while trying to fetch comments "
                              "for ticket: %s", str(exc), str(ticket['id']))
            # check if it's open and there's a comment from a human
            if (ticket['status'] == 'open' and comments.get("count", 0) > 1 and
                    comments['comments'][-1]['metadata']['custom'].get(
                        'author') != TALKTOME_AUTHOR):
                logging.info("last comment in ticket %s is made by a human", str(ticket['id']))
                continue
            # get the user, barcode and ticket id
            user_match = self.username_re.search(ticket['description'])
            barcode_match = self.barcode_re.search(ticket['description'])
            if not (user_match and barcode_match):
                continue
            #user = user_match.group(1)
            user = "said"
            barcode = barcode_match.group(1)
            tickets[ticket['id']] = TicketData(user, barcode, ticket['status'])
        return tickets
