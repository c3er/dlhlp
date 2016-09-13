#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Configuration part ###########################################################

# Path where the files will be saved to.
OUTDIR = 'data'

# An HTML page, containing a list of links to the files of interest.
PAGE_ADDR = 'http://simh.trailing-edge.com/pdf/all_docs.html'

# The file extension(s) of interest.
EXT = '.pdf'
################################################################################

import os.path
import html.parser
import html.entities
import urllib.request

class MarkupReaderBase(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tmpdat = ''
        self._read_data_flag = False
        self.starttags = {}
        self.endtags = {}

    def __enter__(self):
        return self.__class__()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        
    # Properties ###############################################################
    def get_read_data_flag(self):
        return self._read_data_flag
    
    def set_read_data_flag(self, val):
        self._read_data_flag = val
        self.tmpdat = ''
    
    read_data_flag = property(get_read_data_flag, set_read_data_flag)
    ############################################################################
    
    # Inherited from html.parser.HTMLParser ####################################
    def handle_starttag(self, tag, attrs):
        try:
            self.starttags[tag](attrs)
        except KeyError:
            pass

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        try:
            self.endtags[tag]()
        except KeyError:
            pass

    def handle_data(self, data):
        if self.read_data_flag:
            self.tmpdat += data

    def handle_charref(self, name):
        if self.read_data_flag:
            try:
                self.tmpdat += chr(int(name))
            except ValueError:
                self.tmpdat += '&' + str(int(name)) + ';'

    def handle_entityref(self, name):
        if self.read_data_flag:
            self.tmpdat += html.entities.entitydefs[name]
    ############################################################################
    
class LinkReader(MarkupReaderBase):
    def __init__(self):
        super().__init__()
        self.links = []
        self.starttags = {
            'a': self.a_start
        }
        
    def a_start(self, attrs):
        addr = find_attr(attrs, 'href')
        if (addr is not None and
                is_interesting(addr, EXT) and
                addr not in self.links):
            self.links.append(addr)
    
def find_attr(attrs, name):
    for attr, val in attrs:
        if attr == name:
            return val
    return None

def is_interesting(addr, ext):
    if isinstance(ext, str):
        return addr.endswith(ext)
    elif isinstance(ext, (list, tuple)):
        for e in ext:
            if addr.endswith(e):
                return True
        return False

def html2downloads(page):
    page = page.decode('utf_8', 'ignore').strip()
    linecount = len(page.splitlines())
    with LinkReader() as parser:
        parerr = False
        while parser.getpos()[0] < linecount:
            try:
                parser.feed(page)
                if not parerr:
                    break
            except html.parser.HTMLParseError:
                parerr = True
        return parser.links
    
def get_page(addr):
    req = urllib.request.Request(addr)
    req.add_header('User-agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req) as f:
        page = f.read()
    return page
    
# "Main" part ##################################################################
print('Retrieving startpage:', PAGE_ADDR)
page = get_page(PAGE_ADDR)
print('Success')

downloads = html2downloads(page)
for i, addr in enumerate(downloads):
    if not addr.startswith('http'):
        downloads[i] = urllib.parse.urljoin(PAGE_ADDR, addr)

for addr in downloads:
    parts = urllib.parse.urlsplit(addr)
    fname = os.path.basename(parts[2])
    path = os.path.join(OUTDIR, fname)
    
    print('Retrieving file', fname)
    content = get_page(addr)
    with open(path, 'wb') as f:
        f.write(content)
    print('Success')
################################################################################
