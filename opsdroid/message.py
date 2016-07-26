import logging

class Message:
    """ A message object """

    def __init__(self, message, user, room, connector):
        self.message = message
        self.user = user
        self.room = room
        self.connector = connector

    def respond(self, message):
        self.connector.respond(message)
