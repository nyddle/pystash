# -*- coding: utf-8 -*-

import os
import sys

import shelve
import abc
import time

from clint.textui import colored


def output(message, color='white', text_only=False):
    if text_only:
        return str(getattr(colored, color)(message))
    else:
        sys.stdout.write(str(getattr(colored, color)(message)))


class StashedItem():
    """
    Incapsulate all operations with single item from Stash
    """
    def __init__(self, elem, index=None, numbered=False):
        self.elem = elem
        self.value = elem['value']
        if 'tags' in elem:
            self.tags = elem['tags']
        else:
            self.tags = []
        self.is_list = isinstance(elem['value'], list)
        if (index is not None and not self.is_list) or len(elem['value']) <= index:
            raise IndexError
        self.numbered = numbered
        self.index = index

    def get_value(self):
        return self.elem['value'] if not self.index else \
            self.elem['value'][self.index] if not 'marked' in self.elem['meta'] else self.elem['value'][self.index][0]

    def get_tags(self):
        if 'tags' in self.elem:
            return self.elem['tags']
        else:
            return []


    def __repr__(self):
        if self.is_list:
            if 'marked' in self.elem['meta']:
                # it will be uncommented after implementing marked lists
                #result = self.__assemble_marked_list()
                result = self.__assemble_unmarked_list()
            else:
                result = self.__assemble_unmarked_list()
        else:
            result = self.elem['value']
        return '%s\n' % result

    def __assemble_marked_list(self):
        result = []
        template = '{mark} {data}'
        for item in self.elem['value']:
            mark = '+' if item[1] else '-'
            result.append(template.format(mark=mark, data=item[0]))
        return self.list_to_string(result, self.numbered)

    def __assemble_unmarked_list(self):
        result = []
        for item in self.elem['value']:
            result.append(item)
        return self.list_to_string(result, self.numbered)

    @staticmethod
    def list_to_string(items, is_numbered):
        if is_numbered:
            return '\n'.join(['{}. {}'.format(n+1, item) for n, item in enumerate(items)])
        else:
            return '\n'.join(items)


class AbstractStorage(object):
    # todo: update methods signature
    """
    Here will be a docstring
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_connection(self, db):
        pass

    @abc.abstractmethod
    def add(self, key, value, tags):
        """Returns created item as StashedItem"""

    @abc.abstractmethod
    def update(self, item_name, value, index=None):
        """Returns updated item as StashedItem"""

    @abc.abstractmethod
    def delete(self, item_name, index=None):
        """Returns Boolean"""

    @abc.abstractmethod
    def get(self, item_name, index=None):
        """Returns item as  StashedItem"""

    @abc.abstractmethod
    def get_all(self):
        pass

    @abc.abstractmethod
    def is_list(self, item_name):
        pass

    @abc.abstractmethod
    def exist(self, item_name):
        pass

    @abc.abstractmethod
    def get_database_data(self):
        """
        Return whole db data as python dict for sync
        """
        pass


class NotListException(Exception):
    pass


class ShelveStorage(AbstractStorage):
    """
    Storage implementation for work with python shelve library
    """
    DBFILE = os.path.join(os.path.expanduser('~'), '.stash', 'stash.db')

    def __init__(self, db_file=None):
        self.DBFILE = db_file if db_file is not None else self.DBFILE
        path_to_dir = os.path.join('/', *self.DBFILE.split('/')[1:-1])
        if not os.path.exists(path_to_dir):
            os.makedirs(path_to_dir, 0755)
        self.connection = self.get_connection(self.DBFILE)
        if not 'storage' in self.connection:
            self.connection['storage'] = {}
        if not 'last_sync' in self.connection:
            self.connection['last_sync'] = 0
        if not 'last_update' in self.connection:
            self.connection['last_update'] = 0
        self.db = self.connection['storage']
        self.last_sync = self.connection['last_sync']
        self.last_update = self.connection['last_update']

    def get_connection(self, db):
        return shelve.open(db, writeback=True)

    def update(self, item_name, value, tags, index=None, overwrite=False):
        if index is not None:
            index -= 1
            item = self.db[item_name]['value']
            if not isinstance(item, list):
                raise NotListException
            elif index > len(item):
                raise IndexError
            if index == len(item):
                self.db[item_name]['value'].append(value)
            else:
                self.db[item_name]['value'][index] = value
        else:
            if isinstance(self.db[item_name]['value'], list) and not overwrite:
                self.db[item_name]['value'].append(value)
                self.db[item_name]['tags'].append(tags)
            else:
                self.db[item_name]['value'] = value
                self.db[item_name]['tags'] = tags
        self.db[item_name]['updated'] = int(time.time())
        #self.db[item_name]['tags'] = tags
        self.last_update = int(time.time())
        return StashedItem(self.db[item_name], index)

    def delete(self, item_name, index=None):
        if index is not None:
            index -= 1
            if not isinstance(self.db[item_name]['value'], list):
                raise NotListException
            self.db[item_name]['value'].pop(index)
            self.db[item_name]['value']['updated'] = int(time.time())
        else:
            del self.db[item_name]
        self.last_update = int(time.time())
        return True

    def add(self, key, value, tags):
        self.db[key] = {'value': value, 'updated': int(time.time()), 'tags' : tags }
        self.last_update = int(time.time())
        return StashedItem(self.db[key])

    def add_dict(self, newdict):
        self.db.clear()
        for key in newdict:
            self.db[key] = newdict[key]
        self.last_update = int(time.time())
        return


    def exist(self, item_name, index=None):
        if item_name in self.db:
            if index is not None:
                try:
                    self.db[item_name]['value'][index]
                except IndexError:
                    return False
            return True
        return False

    def is_list(self, item_name):
        return isinstance(self.db[item_name]['value'], list)

    def get(self, item_name, index=None):
        index = index - 1 if index is not None else None
        item = self.db[item_name]
        return StashedItem(item, index)

    def get_all(self):
        result = {}
        for k, v in self.db.iteritems():
            result[k] = StashedItem(v)
        return result

    def tags(self, tag):
        result = {}
        for k, v in self.db.iteritems():
            if 'tags' in v:
                if tag in v['tags']:
                    result[k] = StashedItem(v)
        return result

    def alltags(self):
        result = []
        for k, v in self.db.iteritems():
            if 'tags' in v:
                for tag in v['tags']:
                    result.append(tag)
        return result


    def get_database_data(self):
        return dict(self.connection)

    def set_database_data(self, data):
        #TODO check this out
        self.connection['storage'] = data
        return True

