# -*- coding: UTF-8 -*-

import traceback
import logging
from datetime import datetime

from django.db import models
from django.contrib.gis.geos import Point
from django.utils.translation import ugettext_lazy as _

from . import services

AVAILABLE_ATTRIBUTE_KEYS = set('address street name postal_code city locality country language'.split())

class GeocodeSession(models.Model):
    """ Log geocoding activity for debugging and QA.
    """
    started       = models.DateTimeField(_("started"), default=datetime.now)
    finished      = models.DateTimeField(_("finished"), null=True, blank=True)
    job_reference = models.CharField(_("job reference"), max_length=32, db_index=True, default="", blank=True)
    #software_version = models.CharField(max_length=32, default="", blank=True, db_index=True)

    total         = models.PositiveIntegerField(_("total"), default=0)
    completed     = models.PositiveIntegerField(_("completed"), default=0)
    failed        = models.PositiveIntegerField(_("failed"), default=0)
    succeeded     = models.PositiveIntegerField(_("succeeded"), default=0)

    log           = models.TextField(_("log"), default="", blank=True)

    def __unicode__(self):
        return u'{0}: {1}'.format(self.job_reference, self.started)

    def geocode(self, objs, attrs, defaults=None):
        """
            Geocode the given objects, returning a location and the provider.
            attrs is a mapping of attribute names to retrieve data from each obj in objs. Valid keys are listed in AVAILABLE_ATTRIBUTE_KEYS.
            defaults is a dictionary with the same keys, and can be used to speify a fixed value for all objs in the list.
        """
        if not defaults:
            defaults = {}

        # Validate attrs and defaults
        validate_attribute_keys(attrs, 'attrs')
        validate_attribute_keys(defaults, 'defaults')

        self.total = len(objs)
        self.save()

        for obj in objs:
            values = defaults.copy()
            for key, attr in attrs.items():
                val = getattr(obj, attr)
                if val:
                    values[key] = val
            if enough_available_attributes(values):
                res = self.call_geocoders(values)
                self.completed += 1
                if res:
                    self.succeeded += 1
                    location, provider = res
                    self.save()
                    yield obj, location, provider
                else:
                    self.failed += 1
                    self.save()

        self.finished = datetime.now()
        self.save()

    def call_geocoders(self, values):
        """
        return location, provider
        """
        log = [self.log]

        log.append("GEOCODING: {0}".format(values))
        for Geocoder in (services.Yahoo, services.Nominatum ):# services.GoogleMaps, :
            geocoder = Geocoder()
            log.append("  using: {0}".format(geocoder.key))
            try:
                place, (lat, lng) = geocoder.geocode(values)
                log.append("  query: \"{0}\"".format(geocoder.query))
                self.log = "\n".join(log)
                return Point(float(lng), float(lat), srid="WGS84"), geocoder.key
            except services.NoClearResult, e:
                log.append('  ' + unicode(e))
            except ValueError, e:
                tb = traceback.format_exc()
                log.append(tb)
                logging.error(tb)
            if geocoder.query:
                log.append("  query: \"{0}\"".format(geocoder.query))
            log.append("")
    
        log.append("  No result returned\n")
        self.log = "\n".join(log)
    

def validate_attribute_keys(keys, name):
    """ Validate the list of keys to ensure there are no typos.
    """
    for key in keys:
        if key not in AVAILABLE_ATTRIBUTE_KEYS:
            raise ValueError(u"Unknown attribute key provided as {0} to geocoder: \"{1}\".\n"
                             "Available keys: \"{2}\"".format(name, key, 
                                u", ".join(sorted(AVAILABLE_ATTRIBUTE_KEYS))))

def enough_available_attributes(values):
    return any(('city' in values, 'street' in values, 'address' in values))
