from __future__ import unicode_literals

import requests
from apiclient.discovery import build
from django.db.models import signals
from httplib2 import Http
from oauth2client.client import AccessTokenCredentials

from .models import CalendarEvent


class CalendarObserver(object):

    def __init__(self, email, private_key, refresh_token=None,
                 feed=None, client=None):
        """
        Initialize an instance of the CalendarObserver class.
        """
        self.adapters = {}
        self.email = email
        self.refresh_token = refresh_token
        self.private_key = private_key
        self.feed = feed
        self.client = client

    def observe(self, model, adapter):
        """
        Establishes a connection between the model and Google Calendar, using
        adapter to transform data.
        """
        self.adapters[model] = adapter
        signals.post_save.connect(self.on_update, sender=model,
                                  dispatch_uid="djangogcal post-save signal")
        signals.post_delete.connect(self.on_delete, sender=model,
                                    dispatch_uid="djangogcal post-delete signal")

    def observe_related(self, model, related, selector):
        """
        Updates the Google Calendar entry for model when the related model is
        changed or deleted.  Selector should be a function object which accepts
        an instance of related as a parameter and returns an instance of type
        model.
        """
        def on_related_update(**kwargs):
            self.update(model, selector(kwargs['instance']))
        signals.post_save.connect(on_related_update, sender=related, weak=False)
        signals.post_delete.connect(on_related_update, sender=related,
                                    weak=False)

    def on_update(self, **kwargs):
        """
        Called by Django's signal mechanism when an observed model is updated.
        """
        self.get_client()
        self.update(self, kwargs['sender'], kwargs['instance'])

    def on_delete(self, **kwargs):
        """
        Called by Django's signal mechanism when an observed model is deleted.
        """
        self.get_client()
        self.delete(self, kwargs['sender'], kwargs['instance'])

    def get_client(self):
        """
        Get an authenticated calendar api v3 instance.
        """
        token = self.get_access_token()
        if self.client is None:
            credentials = AccessTokenCredentials(token, 'vetware/1.0')
            # credentials = SignedJwtAssertionCredentials(self.email, self.private_key,
            #                                             "https://www.googleapis.com/auth/calendar")
            http = credentials.authorize(Http())
            self.client = build('calendar', 'v3', http=http)
        return self.client

    def get_access_token(self):
        url = "https://accounts.google.com/o/oauth2/token"
        payload = {
            "client_id": self.email,
            "client_secret": self.private_key,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        resp = requests.post(url, data=payload)
        resp_data = resp.json()
        print resp_data
        self.access_token = resp_data['access_token']
        return self.access_token

    def get_event(self, instance, feed=None):
        """
        Retrieves the specified event from Google Calendar, or returns None
        if the retrieval fails.
        """
        if feed is None:
            feed = self.feed
        if self.client is None:
            self.get_client()
        event_id = CalendarEvent.objects.get_event_id(instance, feed)
        try:
            event = self.client.events().get(calendarId=feed, eventId=event_id).execute()
        except Exception:
            event = None
        return event

    def update(self, sender, instance):
        """
        Update or create an entry in Google Calendar for the given instance
        of the sender model type.
        """
        adapter = self.adapters[sender]
        if adapter.can_save(instance):
            client = self.get_client()
            feed = adapter.get_feed_url(instance) or self.feed
            event_data = self.get_event(instance) or {}
            new_event_data = adapter.get_event_data(instance).populate_event(event_data)
            event_id = new_event_data.get('id')
            if event_id:
                client.events().update(calendarId=feed, eventId=event_id,
                                       body=new_event_data).execute()
            else:
                created_event = client.events().insert(calendarId=feed,
                                                       body=new_event_data).execute()
                CalendarEvent.objects.set_event_id(instance, feed,
                                                   created_event['id'])

    def delete(self, sender, instance):
        """
        Delete the entry in Google Calendar corresponding to the given instance
        of the sender model type.
        """
        adapter = self.adapters[sender]
        feed = adapter.get_feed_url(instance) or self.feed
        if adapter.can_delete(instance):
            client = self.get_client()
            event_id = CalendarEvent.objects.get_event_id(instance, feed)
            if event_id:
                client.events().delete(calendarId=feed, eventId=event_id).execute()
        CalendarEvent.objects.delete_event_id(instance, feed)
