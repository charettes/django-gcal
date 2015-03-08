from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import models

try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey


class CalendarEventManager(models.Manager):
    """
    A custom manager for CalendarEvent models, containing utility methods for
    dealing with content-types framework.
    """

    def get_event_id(self, obj, feed_id):
        """
        Gets the Google Calendar event-id for a model, or returns None.
        """
        ct = ContentType.objects.get_for_model(obj)
        try:
            event = self.get(content_type=ct, object_id=obj.pk, feed_id=feed_id)
            event_id = event.event_id
        except models.ObjectDoesNotExist:
            event_id = None
        return event_id

    def set_event_id(self, obj, feed_id, event_id):
        """
        Sets the Google Calendar event-id for a model.
        """
        content_type = ContentType.objects.get_for_model(obj)
        event, created = self.get_or_create(
            content_type=content_type, object_id=obj.pk, feed_id=feed_id, defaults={'event_id': event_id}
        )
        if not created:
            event.event_id = event_id
        return event

    def delete_event_id(self, obj, feed_id):
        """
        Deletes the record containing the event-id for a model.
        """
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=content_type, object_id=obj.pk, feed_id=feed_id).delete()


class CalendarEvent(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey()

    event_id = models.CharField(max_length=255)
    feed_id = models.CharField(max_length=255)

    objects = CalendarEventManager()

    def __unicode__(self):
        return "%s: (%s, %s)" % (self.object, self.feed_id, self.event_id)
