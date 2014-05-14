# -*- coding: utf-8 -*-
from requests.auth import AuthBase
import requests
import json
import hashlib
import sys
import os
import getpass
from clint.textui import colored
from common import output

import netrc

STASH_HOST = 'http://getstash.herokuapp.com'

if 'STASH_HOST' in os.environ:
    STASH_HOST = os.environ['STASH_HOST']

class DuplicateKeyword(Exception):
    """
    Key already exist
    """
    pass


class WrongArgumentsSet(Exception):
    """
    Not enough arguments
    """
    pass


class WrongKey(Exception):
    """
    Key not found
    """
    pass


class NoInternetConnection(Exception):
    """
    No Internet connection or server not available
    """
    pass


class ServerError(Exception):
    """
    Server error
    """
    pass


class UnknownServerError(Exception):
    """
    Unknown server error
    """
    pass


class WrongCredentials(Exception):
    pass


class TokenAuth(AuthBase):
    """Attaches HTTP Token Authentication to the given Request object."""
    def __init__(self, username, password):
        # setup any auth-related data here
        self.username = username
        self.password = password

    def __call__(self, r):
        # modify and return the request
        r.headers['X-Token'] = self.password
        return r


class AlreadyLoggedIn(Exception):
    pass


class API(object):
    username = None
    token = None

    def check_login(self):
        """
        Check if user logged in. If True - return login and token, else returns None
        """
        netrc_path = os.path.join(os.path.expanduser('~'), '.netrc')
        if not os.path.exists(netrc_path):
            open(netrc_path, 'w').close()
        info = netrc.netrc()
        login, account, password = info.authenticators(STASH_HOST) or (None, None, None)
        if password and login:
            if self.username is None or self.token is None:
                self.username = login
                # todo: why token is equal to password?
                self.token = password
            return login, password
        return None

    def login_decorator(fn):
        def wrapper(*args, **kwargs):
            if len(args) > 0 and isinstance(args[0], API):
                if args[0].check_login() is not None:
                    return fn(*args, **kwargs)
            raise Exception('Unknown credentials.\nTry to do stash login at first.\n')
            #output('Unknown credentials.\nTry to do stash login at first.\n', color='yellow')
        return wrapper

    def send_request_decorator(fn):
        """
        Request decorator (avoiding code duplication)
        """
        def wrapper(self, *args):
            data = fn(self, *args)
            data.update(self.get_user_data())
            url = STASH_HOST + '/api/json'
            try:
                data['token'] = self.token
                headers = {'Stash-Token': self.token}
                r = requests.post(url, data=json.dumps(data), headers=headers)
            except requests.exceptions.ConnectionError:
                raise NoInternetConnection
            # todo: replace with regular python exceptions
            if r.status_code == 404:
                raise WrongKey
            if r.status_code == 401:
                raise WrongCredentials
            if r.status_code == 500:
                raise ServerError
            if r.status_code == 200:
                return r.json()
            else:
                return UnknownServerError
        return wrapper

    def get_user_data(self):
        return {'user': self.username}

    def login(self, login, password):
        if self.check_login() is not None:
            raise AlreadyLoggedIn
        m = hashlib.new('md5')
        m.update(password)
        r = self.get_token(login, password)
        #TODO check if r is an error (remove  / from stash host for example) 
        if 'token' in r:
            # todo: maybe we don't need this two lines?
            self.username = login
            self.token = r['token']
            with open(os.path.join(os.environ['HOME'], ".netrc"), "a") as f:
                f.write("machine " + STASH_HOST + " login " + login + " password " + str(r['token']) + "\n")
                f.close()
        else:
            # todo: do something
            pass
        if 'error' in r:
            raise Exception(r['error'])
        return True

    def logout(self):
        """
        Clear .netrc record
        """
        netrc_path = os.path.join(os.path.expanduser('~'), '.netrc')

        if not os.path.exists(netrc_path):
            open(netrc_path, 'w').close()

        info = netrc.netrc()

        if STASH_HOST in info.hosts:
            del info.hosts[STASH_HOST]
        else:
            raise Exception('You haven\'t logged in yet')

        with open(netrc_path, 'w') as f:
            f.write(info.__repr__())
            f.close()
        return True

    # ==========

    @send_request_decorator
    @login_decorator
    def get(self, key):
        return {'get': key}

    @send_request_decorator
    @login_decorator
    def search(self, key):
        return {'search': key}


    @send_request_decorator
    @login_decorator
    def set(self, key, value, tags, overwrite=False,append=False):
        return {'set': { key: value }, 'tags' : tags, 'overwrite': overwrite, 'append' : append}

    @send_request_decorator
    @login_decorator
    def delete(self, key):
        return {'delete': key}

    @send_request_decorator
    @login_decorator
    def all(self):
        return {'getkeys': True}

    @send_request_decorator
    @login_decorator
    def gettags(self):
        return {'gettags': True}

    @send_request_decorator
    @login_decorator
    def tags(self, key):
        return {'tags': key }

    @send_request_decorator
    @login_decorator
    def push(self, list_title, value):
        return {'push': {list_title: value}}

    @send_request_decorator
    def get_token(self, username, password):
        return {'login': {username: password}}

    # =========

    @login_decorator
    @send_request_decorator
    def sync(self, local_db_data):
        return { 'sync' : local_db_data }

    @send_request_decorator
    def get_token(self, username, password):
        return {'login': {username: password}}

    def push(self):
        """Push data to cloud"""

    def pull(self):
        """Pull data from cloud"""
