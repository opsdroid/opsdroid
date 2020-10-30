"""Events for the Telegram Connector."""
from opsdroid import events


class Poll(events.Event):
    """Event class that triggers when a poll is sent."""

    def __init__(self, poll, question, options, total_votes, *args, **kwargs):
        """Contain some attributes that you can access.

        - ``poll`` - The extracted poll details from the payload
        - ``question`` - The question asked in the poll
        - ``options`` - An array containing all options in the poll
        - ``total_votes`` - Sum of total votes that the poll received

        Telegram allows you to create polls or quizzes, this type of message also
        contains a lot of different things that you can access with the ``poll``
        attribute, such as if the poll is closed, if it allows multiple answers, etc.

        """
        super().__init__(*args, **kwargs)
        self.poll = poll
        self.question = question
        self.options = options
        self.total_votes = total_votes


class Contact(events.Event):
    """Event class that triggers when a contact is sent."""

    def __init__(self, contact, phone_number, first_name, *args, **kwargs):
        """Contain some attributes that you can access.

        - ``contact`` - The extracted contact details from the payload
        - ``phone_numer`` - Extracted phone number from contact
        - ``first_name`` - Extracted first name from contact

        Your contact event might contain other information such as the
        contact last name or a ``vcard`` field, you can use the ``contact``
        attribute to access more information if available.

        """
        super().__init__(*args, **kwargs)
        self.contact = contact
        self.phone_number = phone_number
        self.first_name = first_name


class Location(events.Event):
    """Event class that triggers when a location message is sent."""

    def __init__(self, location, latitude, longitude, *args, **kwargs):
        """Contain some attributes that you can access.

        - ``location`` - The extracted location details from the payload
        - ``latitude`` - Extracted latitude from the payload
        - ``longitude`` - Extracted longitude from the payload

        Since Telegram doesn't add any information to the location other than
        the latitude and longitude, you can probably just access these attributes,
        we decided to include the location attribute in case Telegram adds more
        useful things to his message type.

        """
        super().__init__(*args, **kwargs)
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
