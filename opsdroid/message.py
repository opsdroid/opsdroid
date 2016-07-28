""" Class to encapsulate a message """

import logging

class Message:
    """ A message object """

    def __init__(self, text, user, room, connector):
        """ Create object with minimum properties """
        self.text = text
        self.user = user
        self.room = room
        self.connector = connector

    def respond(self, text):
        """ Respond to this message using the connector it was created by """
        self.text = text
        self.connector.respond(self)
