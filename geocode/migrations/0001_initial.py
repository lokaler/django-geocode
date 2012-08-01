# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'GeocodeSession'
        db.create_table('geocode_geocodesession', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('started', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('finished', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('job_reference', self.gf('django.db.models.fields.CharField')(default='', max_length=32, db_index=True, blank=True)),
            ('total', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('completed', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('failed', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('succeeded', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('log', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal('geocode', ['GeocodeSession'])


    def backwards(self, orm):
        
        # Deleting model 'GeocodeSession'
        db.delete_table('geocode_geocodesession')


    models = {
        'geocode.geocodesession': {
            'Meta': {'object_name': 'GeocodeSession'},
            'completed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'failed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_reference': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'db_index': 'True', 'blank': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'started': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'succeeded': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['geocode']
