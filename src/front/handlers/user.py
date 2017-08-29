# -*- coding: utf-8 -*-

import os
import random
import time
import zlib
import uuid
import json
import datetime
import pickle
import binascii
import base64
from twisted.internet import defer
from twisted.python import log
from cyclone import escape, web
from front import storage
from front import utils
from front.utils import E
from passlib.apps import custom_app_context as pwd_context
from front.D import USERINIT, PREFIX, POSTFIX
from itertools import *
# from front.handlers.base import BaseHandler
from front.wiapi import *
from front.handlers.base import ApiHandler, ApiJSONEncoder
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from front.utils import E
from front.wiapi import *
from front import D
from cyclone import web, escape

@handler
class RegisterHandler(ApiHandler):
    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('User register', '/user/register/', [
        Param('username', True, str, 'putaogame', 'putaogame', 'username'),
        Param('password', True, str, 'putaogame', 'putaogame', 'password'),
    ], filters=[ps_filter], description="User register")
    def get(self):
        try:
            username = self.get_argument("username")
            password = self.get_argument("password")
        except Exception:
            raise web.HTTPError(400, "Argument error")
        res = yield self.sql.runQuery(
            "SELECT id, username, password_hash FROM core_user WHERE username=%s AND password_hash=%s LIMIT 1",
            (username, pwd_context.encrypt(password)))
        if not res:
            username = username
            password_hash = pwd_context.encrypt(password)
            access_token = binascii.hexlify(os.urandom(20)).decode()
            refresh_token = binascii.hexlify(os.urandom(20)).decode()
            created = int(time.time())
            modified = int(time.time())
            query = "INSERT INTO core_user(username, password, access_token, refresh_token, created, modified)" \
                    " VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"
            params = (username, password_hash, access_token, refresh_token, created, modified)
            for i in range(5):
                try:
                    sql = yield self.sql.runOperation(query, params)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    sql = None
                    continue

            if sql:
                user_id = sql[0][0]
                self.redis.set('access_token:%s' % access_token, user_id, ex=D.EXPIRATION)
                self.write(dict(user_id=user_id, access_token=access_token, refresh_token=refresh_token))
                return
            else:
                self.write(dict(err=E.ERR_USER_CREATED, msg=E.errmsg(E.ERR_USER_CREATED)))
                return
        else:
            self.write(dict(err=E.ERR_USER_REPEAT, msg=E.errmsg(E.ERR_USER_REPEAT)))
            return

@handler
class LoginHandler(ApiHandler):
    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('User login', '/user/login/', [
        Param('username', False, str, 'putaogame', 'putaogame', 'username'),
        Param('password', False, str, 'putaogame', 'putaogame', 'password'),
        Param('user_id', False, str, '1', '1', 'user_id'),
        Param('_access_token', False, str, 'putaogame', 'putaogame', '_access_token'),
        Param('_refresh_token', False, str, 'putaogame', 'putaogame', '_refresh_token'),
    ], filters=[ps_filter], description="User login")
    def get(self):
        try:
            username = self.get_argument("username", None)
            password = self.get_argument("password", None)
            user_id = self.get_argument("user_id", None)
            access_token = self.get_argument("access_token", None)
            refresh_token = self.get_argument("refresh_token", None)
        except Exception:
            self.write(dict(err=E.ERR_ARGUMENT, msg=E.errmsg(E.ERR_ARGUMENT)))
            return
        if username and password:
            query = "SELECT id, username, password_hash, access_token, refresh_token FROM core_user WHERE username=%s AND" \
                    " password_hash=%s LIMIT 1"
            r = yield self.sql.runQuery(query, (username, pwd_context.encrypt(password)))
            if r:
                user_id, username, password_hash, _access_token, _refresh_token = r[0]
                access_token_redis = self.redis.get('access_token:%s' % access_token)
                if not access_token_redis:
                    access_token = binascii.hexlify(os.urandom(20)).decode()
                    refresh_token = binascii.hexlify(os.urandom(20)).decode()
                    query = "UPDATE core_user SET access_token=%s, refresh_token=%s, modified=%s WHERE id=%s"
                    params = (access_token, refresh_token, int(time.time()))
                    for i in range(5):
                        try:
                            yield self.sql.runOperation(query, params)
                            break
                        except storage.IntegrityError:
                            log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                            continue
                self.redis.set('access_token:%s' % access_token, user_id, ex=D.EXPIRATION)
                self.write(dict(user_id=user_id, access_token=access_token, refresh_token=refresh_token))
                return
            else:
                self.write(dict(err=E.ERR_USER_PASSWORD, msg=E.errmsg(E.ERR_USER_PASSWORD)))
                return
        elif access_token and user_id:
            query = "SELECT id, username, password_hash, access_token, refresh_token FROM core_user WHERE user_id=%s AND" \
                    " access_token=%s LIMIT 1"
            r = yield self.sql.runQuery(query, (user_id, access_token))
            if r:
                user_id, username, password_hash, access_token, refresh_token = r[0]
                access_token_redis = self.redis.get('access_token:%s' % access_token)
                if not access_token_redis:
                    if refresh_token:
                        pass
                    else:
                        self.write(dict(err=E.ERR_USER_TOKEN_EXPIRE, msg=E.errmsg(E.ERR_USER_TOKEN_EXPIRE)))
                        return
                access_token = binascii.hexlify(os.urandom(20)).decode()
                refresh_token = binascii.hexlify(os.urandom(20)).decode()
                query = "UPDATE core_user SET access_token=%s, refresh_token=%s, modified=%s WHERE id=%s"
                params = (access_token, refresh_token, int(time.time()))
                for i in range(5):
                    try:
                        yield self.sql.runOperation(query, params)
                        break
                    except storage.IntegrityError:
                        log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                        continue
                self.redis.set('access_token:%s' % access_token, user_id, ex=D.EXPIRATION)
                self.write(dict(user_id=user_id, access_token=access_token, refresh_token=refresh_token))
                return

            else:
                self.write(dict(err=E.ERR_USER_TOKEN, msg=E.errmsg(E.ERR_USER_TOKEN)))
                return
        else:
            self.write(dict(err=E.ERR_ARGUMENT, msg=E.errmsg(E.ERR_ARGUMENT)))
            return
