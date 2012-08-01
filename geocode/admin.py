# -*- coding: UTF-8 -*-

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import GeocodeSession

class GeocodeSessionAdmin(admin.ModelAdmin):
    list_display = ('started', 'finished', 'job_reference', 'total', 'completed', 'failed', 'succeeded')
    readonly_fields = ('started', 'finished', 'job_reference', 'total', 'completed', 'failed', 'succeeded', 'html_log')
    exclude = ('log',)

    def html_log(self, instance):
        return u"<pre>{0}</pre>\n".format(instance.log)
    html_log.allow_tags = True
    html_log.short_description = _("log")

admin.site.register(GeocodeSession, GeocodeSessionAdmin)
