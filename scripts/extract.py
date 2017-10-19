#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Smyrna epigraphic content from HTML to XML
"""

import better_exceptions
from airtight.cli import configure_commandline
from airtight.logging import flog
from bs4 import BeautifulSoup as bs
import logging
from nltk.tokenize import RegexpTokenizer
from polyglot.detect import Detector
from polyglot.detect.base import UnknownLanguage
import re
import sys

RX_APP = re.compile('^\d.+')

TOKENIZER = RegexpTokenizer(r'\w+')     # splits strings into invidual words

DEFAULT_LOG_LEVEL = logging.WARNING
OPTIONAL_ARGUMENTS = [
    ['-l', '--loglevel', 'NOTSET',
        'desired logging level (' +
        'case-insensitive string: DEBUG, INFO, WARNING, or ERROR',
        False],
    ['-v', '--verbose', False, 'verbose output (logging level == INFO)',
        False],
    ['-w', '--veryverbose', False,
        'very verbose output (logging level == DEBUG)', False],
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help
    ['source', str, 'html file to read']
]

def parse_graffiti(soup):
    start = soup.find_all('p', class_='s3', text='The Graffiti')[0]
    with open('fodder/epidoc-template.xml', 'r') as f:
        epidoc = f.read()
    # get a list of nodes inside the Graffiti chapter
    nodes = []
    for sib in start.next_siblings:
        if sib.name == 'p':
            try:
                class_val = sib['class']
            except KeyError:
                pass
            else:
                if 's3' in class_val:
                    break
        nodes.append(sib)
    contexts = {}
    d = None
    for node in nodes:
        if node.name == 'p':
            try:
                class_val = node['class']
            except KeyError:
                pass
            else:
                if 's7' in class_val:
                    title = node.text
                    #print(title)
                    slug = title.lower()
                    if '[' in slug:
                        slug = slug.split('[')[0]
                    if '(' in slug:
                        slug = slug.split()[0]
                    slug = '-'.join(slug.split())
                    d = {
                        'title': title,
                        'nodes': []
                    }
                    contexts[slug] = d
        # discard initial paragraphs until we get our first inscription
        try:
            d['nodes'].append(node)
        except TypeError:
            pass
    for k, v in contexts.items():
        # print(v['title'])
        v['graffiti'] = {}
        d = None
        for node in v['nodes'][1:]:
            if node.name == 'h2':
                if d is not None:
                    for n in d['nodes']:
                        print(n.text)
                    parse_graffito(d)
#                     try:
#                         d['text']
#                     except KeyError:
#                         print('no text in this entry')
#                     else:
#                         text_lines = ''
#                         for i, t in enumerate(d['text']):
#                             text_lines += str(
#                                 '\n                    <lb n="{}"/>{}'
#                                 ''.format(i, t))
#                         z = epidoc.format(
#                             text_title='{}: {}'.format(
#                                 id, d['title']),
#                             text_id=id,
#                             text=text_lines)
#                         print(z)
#                     result = input('continue?')
#                     if result[0].lower() != 'y':
#                         sys.exit(0)
                heading = node.text
                heading = heading.split()
                id = heading[0]
                title = ' '.join(heading[1:]).lower().replace('—', ': ')
                # print('\tid: {}'.format(id))
                # print('\ttitle: {}'.format(title))
                d = {
                    'title': title,
                    'nodes': []
                }
                v['graffiti'][id] = d
            try:
                d['nodes'].append(node)
            except TypeError:
                pass
    for k, v in contexts.items():
        flog(k)
        flog(v['title'])
        for id, graffito in v['graffiti'].items():
            # print('\t{}'.format(id))
            flog(id)
            flog(graffito['title'])

            # print_graffito(id, graffito)

    for c_id, c in contexts.items():
        for g_id, g in c['graffiti'].items():
            try:
                description = g['description']
            except KeyError:
                description = ''
            else:
                text_lines = ''
                if len(description) > 1:
                    for i, t in enumerate(description):
                        text_lines += str(
                            '\n                    <lb/>{}'.format(t))
                else:
                    text_lines = description[0]
                description = text_lines
            try:
                text = g['text']
            except KeyError:
                text = ''
            else:
                text_lines = ''
                for i, t in enumerate(text):
                    text_lines += str(
                        '\n                    <lb/>{}'.format(t))
                text_lines = text_lines.replace(
                    '- ', '\n                    <lb break="no"/>')
                text = text_lines
            try:
                translation = g['translation']
            except KeyError:
                translation = ''
            else:
                text_lines = ''
                if len(translation) > 1:
                    text_lines = ' '.join(translation)
                else:
                    text_lines = translation[0]
                text_lines = text_lines.replace('- ', '')
                translation = text_lines
            try:
                commentary = g['commentary']
            except KeyError:
                commentary = ''
            else:
                text_lines = ''
                if len(commentary) > 1:
                    text_lines = ' '.join(commentary)
                else:
                    text_lines = commentary[0]
                text_lines = text_lines.replace('- ', '')
                commentary = text_lines
            z = epidoc.format(
                text_title='{}: {}'.format(
                    g_id, g['title']),
                text_id=g_id,
                description=description,
                text=text,
                translation=translation,
                commentary=commentary)
            slug = g_id.lower().replace(' ', '-')
            fn = 'output/{}.xml'.format(slug)
            fn = fn.replace('..', '.')
            with open(fn, 'w') as f:
                f.write(z)
            fn = 'output/{}.txt'.format(slug)
            fn = fn.replace('..', '.')
            with open(fn, 'w') as f:
                for n in g['nodes']:
                    f.write(n.text + '\n')



def print_graffito(id, g):
    print('{}: {}'.format(id, g['title']))
    for part in [
        'description', 'images', 'text', 'translation', 'apparatus',
        'commentary']:
        try:
            lines = g[part]
        except KeyError:
            pass
        else:
            print(part)
            for i, line in enumerate(lines):
                if part == 'apparatus':
                    print('\t{}: {}'.format(i+1, line))
                else:
                    print('\t{}'.format(line))


def parse_graffito(g):
    global TOKENIZER
    #print('\t\ttitle: {}'.format(g['title']))
    heading_count = 0
    break_count = 0
    image_count = 0
    for node_i, node in enumerate(g['nodes']):

        # ignore headings
        if node.name == 'h2':
            heading_count += 1
            continue

        # ignore paragraphs containing only line breaks
        if (
            node.name == 'p' and len(node.contents) == 1 and
            node.br is not None):
            break_count += 1
            continue

        # capture image filenames
        images = node.find_all('img')
        if len(images) > 0:
            for image in images:
                src = image['src']
                try:
                    g['images'].append(src)
                except KeyError:
                    g['images'] = [src]
                image_count += 1
            continue

        # capture sequentially formatted apparatus
        if node.name == 'ol':
            try:
                g['text']
            except KeyError:
                msg = (
                    'found sequential apparatus (ol), but no text yet '
                    'identified: "{}"'.format(node.text))
                raise ValueError(msg)
            g['apparatus'] = [
                '{}: {}'.format(i, li.text) for i, li in enumerate(node.li)]
            continue

        # process actual paragraphs of content
        if node.name == 'p':
            para_type = ''
            text = node.text

            # capture paragraph types with obvious formatting
            m = RX_APP.match(text)
            if m is not None:
                para_type = 'apparatus'
            elif text[0] == '“' and text[-1] == '”':
                para_type = 'translation'
            elif text.startswith('Bibliography: '):
                para_type = 'bibliography'
            elif text.startswith('detail of'):
                para_type = 'caption'
            else:
                try:
                    detector = Detector(text)
                except UnknownLanguage as msg:
                    flog(msg, comment='detector failure message: ')
                else:
                    flog(detector.reliable, comment='detector reliable? ')
                    if detector.reliable:
                        flog(detector.language.code, comment='detector language')
                        if detector.language.code == 'en':
                            if 'text' not in g.keys():
                                para_type = 'description'
                            else:
                                para_type = 'commentary'
                        else:
                            para_type = 'text'
                if para_type == '':
                    if (
                        '- ' in text
                        or 'Tύχη' in text
                        or ' ̣ ' in text
                        or ']Ṃ' == text
                        or 'Π (or Γ) ΠΕ̣' == text
                        or '[[ ]]' == text
                        or '̣ ̣ ̣' in text
                        or 'se' == text):
                        para_type = 'text'
                    else:
                        words = TOKENIZER.tokenize(text.lower())
                        for word in words:
                            if word in [
                                'dimensions', 'wide', 'high', 'dipinto', 'graffito',
                                'incised', 'inscription', 'majuscule', 'preserved']:
                                para_type = 'description'
                                break
                        if para_type == '':
                            for word in words:
                                if word in [
                                    'traces', 'stars', 'space', 'unread']:
                                    para_type = 'text'
                        if para_type == '' and 'description' in g.keys():
                            para_type = 'text'
                        if para_type == '' and text in g.keys():
                            para_type = 'text'
                        if para_type == 'description' and 'text' in g.keys():
                            para_type == 'commentary'
#                        if para_type != 'description' and 'description' in g.keys():
#                            para_type = 'text'
            print('<<< {} >>> {}'.format(para_type, text))
            if para_type == 'apparatus':
                try:
                    g['apparatus'].append(text)
                except KeyError:
                    g['apparatus'] = [text]
#                flog(g['apparatus'])
            elif para_type == 'caption':
                try:
                    g['caption'].append(text)
                except KeyError:
                    g['caption'] = [text]
            elif para_type == 'text':
                try:
                    g['text'].append(text)
                except KeyError:
                    g['text'] = [text]
                flog(g['text'])
            elif para_type == 'description':
                try:
                    g['description'].append(text)
                except KeyError:
                    g['description'] = [text]
                flog(g['description'])
            elif para_type == 'translation':
                try:
                    g['translation'].append(text)
                except KeyError:
                    g['translation'] = [text]
                flog(g['translation'])
            elif para_type == 'bibliography':
                g['bibliography'] = ':'.join(text.split(':')[1:])
                flog(g['bibliography'])
            elif para_type == 'commentary':
                try:
                    g['commentary'].append(text)
                except KeyError:
                    g['commentary'] = [text]
                flog(g['commentary'])
            else:
                print('\t\t\tunclassified paragraph: "{}"'.format(text))
                sys.exit(-1)


#        print('\tbefore: {}'.format(len(v['nodes'])))






#        v['nodes'] = [
#            node for node in v['nodes']
#            if len(node.contents) > 1 or node.contents[0].name == 'br']
#        print('\tafter: {}'.format(len(v['nodes'])))


def main(**kwargs):
    """
    main function
    """
    # logger = logging.getLogger(sys._getframe().f_code.co_name)
    with open(kwargs['source'], 'r') as f:
        soup = bs(f, 'html.parser')
    parse_graffiti(soup)


if __name__ == "__main__":
    main(**configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL))
