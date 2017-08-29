from django.contrib import admin
import simplejson as json
from django.utils.translation import ugettext_lazy as _
from models import *


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'password_hash')


admin.site.register(User, UserAdmin)
