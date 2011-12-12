#!/usr/bin/env python

"""
Utility for bulk converting Delicious bookmark export files to RDF,
using the following ontologies for bookmark and tag representation:

	http://www.w3.org/2002/01/bookmark#
        http://www.holygoak.co.uk/owl/redwood/0.1/tags

* Usable as library for obtaining RDFLib graph represenation of a given
  Delicious export file's contents, or as script to print out the same
  graph to stdout (see --help option for details).

* Allows output to any serialization format supported by RDFLib, with
  default being N3.

#########################################################################
Copyright (c) 2011, Ian Mondragon
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
  
* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation 
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
POSSIBILITY OF SUCH DAMAGE.
############################################################################
"""

from optparse import OptionParser
import sys, time
import datetime

from BeautifulSoup import BeautifulSoup
import rdflib
from rdflib import RDF, RDFS


__author__ = 'Ian Mondragon'
__version__ = 0.1

# external ontologies
BOOKMARK = rdflib.Namespace('http://www.w3.org/2002/01/bookmark#')
TAGS = rdflib.Namespace('http://www.holygoat.co.ok/owl/redwood/0.1/tags/')

#---------------------------------------------------------------------------
# Delicious bookmark extraction
#---------------------------------------------------------------------------

def parseBookmark(link):
    '''Parses a Delicious bookmark from a BeautifulSoup link
    
    :param link: a BeautifulSoup link
    :returns: tuple of (uri, date, title, tag-list)
    :rtype: tuple
    '''
    uri = link['href']
    date = datetime.datetime(*time.localtime(float(link['add_date']))[:6])
    tags = link['tags'].split(',')
    title = link.contents[0].__str__('utf-8')
    return (uri, date, title, tags)

def extractBookmarks(filename):
    '''Returns a list of tuples representing each bookmark in
    the provided Delicious bookmark export file.
    
    :param filename: a Delicious bookmark export file
    :returns: list of tuples
    :rtype: list
    '''
    content = open(filename).read()
    soup = BeautifulSoup(content)
    links = soup.findAll('a')
    bookmarks = [parseBookmark(link) for link in links]
    return bookmarks

#---------------------------------------------------------------------------
# RDF transformation
#---------------------------------------------------------------------------

def addBookmark(graph, tagns, (uri, date, title, tags)):
    '''Adds the decomposed Delicious bookmark to the provided graph.

    :param graph: an rdflib graph
    :param tagns: the target tag namespace (as a string)
    :param (uri, date, title, tags): decomposed Delicious bookmark
    '''
    resource = rdflib.URIRef(uri)
    _NS = rdflib.Namespace(tagns)
    graph.add((resource, RDF.type, BOOKMARK.Bookmark))
    graph.add((resource, RDFS.label, rdflib.Literal(title)))
    graph.add((resource, TAGS.taggedOn, rdflib.Literal(date)))
    for x in tags:
        graph.add((resource, TAGS.taggedWithTag, _NS[x]))
    return graph
    
def bookmarkGraph(filename, tagns):
    '''Constructs and populates an RDFLib graph with the contents of the
    provided Delicious bookmark export file.

    :param filename: a Delicious bookmark export file
    :param tagns: the target tag namespace (as a string)
    :returns: an RDFLib graph
    :rtype: rdflib.ConjunctiveGraph
    '''
    bookmarks = extractBookmarks(filename)
    graph = rdflib.ConjunctiveGraph()
    for x in bookmarks:
        addBookmark(graph, tagns, x)
    return graph

if __name__ == '__main__':
    
    # set up option parser
    parser = OptionParser()
    parser.add_option('-f', '--file', dest='filename', action='store',
                      help='Delicious bookmark export file')
    parser.add_option('-t', '--tagns', dest='tagns', action='store',
                      help='Tag namespace')
    parser.add_option('-o', '--output', dest='output', action='store',
                      help='Output format (xml, nt, n3)', default='n3')

    # extract bookmarks from provided file, serialize graph to stdout
    (options, args) = parser.parse_args()
    graph = bookmarkGraph(options.filename, options.tagns)
    print graph.serialize(format=options.output)
