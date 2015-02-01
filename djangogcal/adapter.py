"""
djangogcal.adapter


"""

from datetime import datetime

from atom.data import Content, Title
from gdata.data import Reminder
from gdata.calendar.data import When, CalendarWhere, EventWho
from django.utils.tzinfo import FixedOffset, LocalTimezone

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'


def format_datetime(date):
    """
    A utility method that converts the datetime to UTC serialized
    for Google Calendar.
    """
    local = date.replace(tzinfo=LocalTimezone(date))
    return local.astimezone(FixedOffset(0)).strftime(DATE_FORMAT)


class CalendarEventData(object):
    """
    A data-structure which converts Python data-types into Google Data API
    objects which can be transmitted to Google services.
    """
    
    def __init__(self, start, end, attendees, title="", description=None, location=None,
                 reminder_minutes=None, reminder_method="popup"):
        """
        Instantiates a new instance of CalendarEventData.
        """
        self.start = start
        self.end = end
        self.title = title
        self.location = location
        self.attendees = attendees
        self.description = description
        self.reminder_minutes = reminder_minutes
        self.reminder_method = reminder_method

    def populate_event(self, event_data={}):
        """
        Populates the parameters of a Google Calendar event object.
        """

        new_event_data = {
            'summary': self.title,
            'location': self.location,
            'description': self.description,
            'start': {
                'dateTime': format_datetime(self.start)
            },
            'end': {
                'dateTime': format_datetime(self.end)
            },
            # 'attendees': [{'email': attendee} for attendee in self.attendees],
        }
        if self.reminder_minutes:
            new_event_data['reminders'] = {
                'useDefault': False,
                'overrides': [{
                    'method': self.reminder_method,
                    'minutes': str(self.reminder_minutes)
                }]
            }
        event_data.update(new_event_data)
        return event_data


class RawCalendarEventData(object):
    """
    A data-structure which accepts Google Calendar data types, for users who
    need access to advanced fields.
    """
    
    def __init__(self, when, **kwargs):
        """
        Instantiates a new instance of RawCalendarEventData.
        """
        self.when = when
        self.kwargs = kwargs
    
    def populate_event(self, event):
        """
        Populates the parameters of a Google Calendar event object.
        """
        event.when = self.when
        for key in self.kwargs:
            setattr(event, key, self.kwargs[key])

class CalendarAdapter(object):
    """
    
    """
    
    def __init__(self):
        """
        Instantiates a new instance of CalendarAdapter.
        """
        pass
    
    def can_save(self, instance):
        """
        Should return a boolean indicating whether the object can be stored or
        updated in Google Calendar.
        """
        return True
    
    def can_delete(self, instance):
        """
        Should return a boolean indicating whether the object can be deleted
        from Google Calendar.
        """
        return True

    def can_notify(self, instance):
        """
        Should return a boolean indicating whether Google Calendar should send
        event change notifications.
        """
        return False
    
    def get_event_data(self, instance):
        """
        This method should be implemented by users, and must return an object
        conforming to the CalendarEventData protocol.
        """
        raise NotImplementedError()

    def get_feed_url(self, instance):
        """
        This method may be implemented by users, and should return a string to 
        be used to specify the feed for the event.
        """
        raise None
    
