""" Class to encapsulate a message """

import logging

class Message:
    """ A message object """

    def __init__(self, message, user, room, connector):
        """ Create object with minimum properties """
        self.message = message
        self.user = user
        self.room = room
        self.connector = connector

    def respond(self, message):
        """ Respond to this message using the connector it was created by """
        self.connector.respond(message)
