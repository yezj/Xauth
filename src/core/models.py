# -*- coding: utf-8 -*-
import binascii
import os
import datetime
import hashlib
from django.db import models
from django.utils.text import ugettext_lazy as _
from cyclone import escape
from signals import *
from positions import PositionField
from django.core.exceptions import ValidationError
from filebrowser.fields import FileBrowseField, FileObject
from django.contrib.auth.models import User as AdminUser
from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

from back.settings import SECRET_KEY


class User(models.Model):
    username = models.CharField(_('Username'), max_length=32, unique=True)
    password_hash = models.CharField(_('Password_hash'), max_length=128, blank=True)
    access_token = models.CharField(_('Access_token'), max_length=128, unique=True)
    refresh_token = models.CharField(_('Refresh_token'), max_length=128, unique=True)
    created = models.PositiveIntegerField(_('Created'), default=0, db_index=True)
    modified = models.PositiveIntegerField(_('Modified'), default=0, db_index=True)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)
        return self.password_hash

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __unicode__(self):
        return self.username
