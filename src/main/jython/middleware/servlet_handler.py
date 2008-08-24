import os
import sys
import time
import traceback
import urllib

from pprint import pformat

from django import http
from django.core import signals
from django.core.handlers.base import BaseHandler
from django.dispatch import dispatcher
from django.utils import datastructures
from django.utils.encoding import force_unicode

def headers_dict_from_request(req):
    res = {}
    for key in req.getHeaderNames():
        value = req.getHeader(key)
        res[key] = value
    return res

class ServletRequest(http.HttpRequest):
    def __init__(self, req):
        self._req = req
        self.path = force_unicode(urllib.unquote(req.getRequestURI()))

    def __repr__(self):
        try:
            get = pformat(self.GET)
        except Exception, e:
            get = '<could not parse> {%s}' % e
        try:
            post = pformat(self.POST)
        except Exception, e:
            traceback.print_exc()
            post = '<could not parse> {%s}' % e
        try:
            cookies = pformat(self.COOKIES)
        except Exception, e:
            cookies = '<could not parse> {%s}' % e
        try:
            meta = pformat(self.META)
        except Exception, e:
            traceback.print_exc()
            meta = '<could not parse> {%s}' % e
        return '<ServletRequest\npath:%s,\nGET:%s,\nPOST:%s\nCOOKIES:%s,\nMETA:%s>' % \
            (self.path, get, post, cookies, meta)

    def get_full_path(self):
        return '%s%s' % (self.path, self._req.getQueryString() and ('?' + self._req.getQueryString()) or '')

    def _load_post_and_files(self):
        contenttype = self._req.getHeader('content-type')
        if contenttype is not None and contenttype.startswith('multipart'):
            self._post, self._files = http.parse_file_upload(headers_dict_from_request(self._req), self.raw_post_data)
        else:
            self._post, self._files = http.QueryDict(self.raw_post_data, encoding=self.encoding), datastructures.MultiValueDict()

    def _get_request(self):
        if not hasattr(self, '_request'):
            self._request = datastructures.MergeDict(self.POST, self.GET)
        return self._request

    def _get_get(self):
        if not hasattr(self, '_get'):
            qs = self._req.getQueryString()
            self._get = http.QueryDict(qs, encoding=self.encoding)
        return self._get

    def _set_get(self, get):
        self._get = get

    def _get_post(self):
        if not hasattr(self, '_post'):
            self._load_post_and_files()
        return self._post

    def _set_post(self, post):
        self._post = post

    def _get_cookies(self):
        if not hasattr(self, '_cookies'):
            cookies = self._req.getHeader('cookie') or ''
            self._cookies = http.parse_cookie(cookies)
        return self._cookies

    def _set_cookies(self, cookies):
        self._cookies = cookies

    def _get_files(self):
        if not hasattr(self, '_files'):
            self._load_post_and_files()
        return self._files

    def _get_meta(self):
        if not hasattr(self, '_meta'):
            self._meta = {
                'AUTH_TYPE': self._req.getAuthType(),
                'CONTENT_LENGTH': self._req.getContentLength(),
                'CONTENT_TYPE': self._req.getContentType(),
                'GATEWAY_INTERFACE': 'CGI/1.1', # hmmmm?
                'PATH_INFO': self._req.getPathInfo(),
                'PATH_TRANSLATED': self._req.getPathTranslated(),
                'QUERY_STRING': self._req.getQueryString(),
                'REMOTE_ADDR': self._req.getRemoteAddr(),
                'REMOTE_HOST': self._req.getRemoteHost(),
                'REMOTE_IDENT': '', # ???????????
                'REMOTE_USER': self._req.getRemoteUser(),
                'REQUEST_METHOD': self._req.getMethod(),
                'SCRIPT_NAME': None,
                'SERVER_NAME': self._req.getServerName(),
                'SERVER_PORT': self._req.getServerPort(),
                'SERVER_PROTOCOL': self._req.getProtocol(),
                'SERVER_SOFTWARE': 'django+jython servlet'
                }
            for key in self._req.getHeaderNames():
                value = self._req.getHeader(key)
                key = 'HTTP_' + key.upper().replace('-', '_')
                self._meta[key] = value
        return self._meta

    def _get_raw_post_data(self):
        if not hasattr(self, '_raw_post_data'):
            self._raw_post_data = ''
            r = self._req.getReader()
            c = r.read()
            while (c != -1):
                self._raw_post_data += chr(c)
                c = r.read()
        return self._raw_post_data

    def _get_method(self):
        return self.META['REQUEST_METHOD'].upper()

    def _get_path_info(self):
        return self.META['PATH_INFO']

    def is_secure(self):
        return self._req.isSecure()

    GET = property(_get_get, _set_get)
    POST = property(_get_post, _set_post)
    COOKIES = property(_get_cookies, _set_cookies)
    FILES = property(_get_files)
    META = property(_get_meta)
    REQUEST = property(_get_request)
    raw_post_data = property(_get_raw_post_data)
    method = property(_get_method)
    path_info = property(_get_path_info)

class ServletHandler(BaseHandler):
    request_class = ServletRequest

    def __call__(self, req, resp):
        from django.conf import settings

        if self._request_middleware is None:
            self.load_middleware()

        #dispatcher.send(signal=signals.request_started)
        signals.request_started.send(sender=self.__class__)
        try:
            try:
                request = self.request_class(req)
            except UnicodeDecodeError:
                response = http.HttpResponseBadRequest()
            else:
                response = self.get_response(request)

                for middleware_method in self._response_middleware:
                    response = middleware_method(request, response)
                response = self.apply_response_fixes(request, response)

                print '[%s] "%s %s %s" %s %s' % (time.strftime('%d/%b/%Y %H:%M:%S'),
                                                 request.method, req.getRequestURI(), 
                                                 request.META['SERVER_PROTOCOL'],
                                                 response.status_code, 
                                                 sum([len(i) for i in response]))
        finally:
            #dispatcher.send(signal=signals.request_finished)
            signals.request_finished.send(sender=self.__class__)

        resp.setHeader('Content-Type', response['Content-Type'])
        for key, value in response.items():
            if key.lower() != 'content-type':
                resp.addHeader(key, value)
        for c in response.cookies.values():
            resp.addHeader('Set-Cookie', c.output(header=''))
        resp.setStatus(response.status_code)

        try:
            out = resp.getWriter()
            for chunk in response:
                out.write(chunk)
        finally:
            out.close()
                 
def handler(req, resp):
    return ServletHandler()(req, resp)
