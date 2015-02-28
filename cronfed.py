
# Credit to Mark Williams for this
import re
import uuid
import socket
import argparse
from contextlib import closing
from collections import namedtuple
import xml.etree.cElementTree as ET

from boltons.mboxutils import mbox_readonlydir


FEED_TITLE = 'Cronfed'
DEFAULT_LINK = 'http://hatnote.com'
DEFAULT_DESC = 'Fresh cron output from cronfed'
DEFAULT_TITLE = 'Cronfed on %s' % socket.gethostname()
EXCLUDE_TAGS = set(['lastBuildDate'])
GUID_URL_TMPL = 'http://hatnote.com/{guid}'


DEFAULT_SUBJECT_PARSER = re.compile(
    'Cron <(?P<user>[^@].+)@(?P<host>[^>].+)> (?P<command>.*)')
DEFAULT_SUBJECT_RENDERER = 'cron: <%(user)s@%(host)s> %(command)s'
MESSAGE_ID_PARSER = re.compile('<(?P<id>[^@]+)@(?P<host>[^>+]+)>')


def find_python_error_type(text):
    from tbutils import ParsedTB
    try:
        tb_str = text[text.index('Traceback (most recent'):]
    except ValueError:
        raise ValueError('no traceback found')
    parsed_tb = ParsedTB.from_string(tb_str)
    return parsed_tb.exc_type


BaseRSSItem = namedtuple('RSSItem', ['title', 'description', 'link',
                                     'lastBuildDate', 'pubDate', 'guid'])


class RSSItem(BaseRSSItem):
    @classmethod
    def fromemail(cls, email, excludes=(),
                  redacted='REDACTED',
                  parser=DEFAULT_SUBJECT_PARSER,
                  renderer=DEFAULT_SUBJECT_RENDERER):
        match = parser.match(email.get('subject'))
        if not match:
            raise ValueError("Unparseable subject")
        parsed = match.groupdict()

        for exclude in excludes:
            parsed[exclude] = redacted
        lastBuildDate = pubDate = email.get('date')
        title = renderer % parsed

        match = MESSAGE_ID_PARSER.match(email.get('message-id'))
        if not match:
            guid = uuid.uuid4()
        else:
            guid = match.group('id')
        body = email.get_payload()

        desc = 'Cron ran %s at %s.' % (parsed['command'], pubDate)
        try:
            python_error_type = find_python_error_type(body)
        except:
            python_error_type = None
        if python_error_type:
            desc += ' Check for a Python exception: %s.' % python_error_type

        if body:
            desc += ' Command output:\n\n' + summarize(body, 16)

        return cls(title=title, description=desc, link=None,
                   lastBuildDate=lastBuildDate, pubDate=pubDate, guid=guid)


def summarize(text, length):
    """
    Length is the amount of text to show. It doesn't include the
    length that the summarization adds back in."
    """
    len_diff = len(text) - length
    if len_diff <= 0:
        return text
    return ''.join([text[:length/2],
                    '... (%s bytes) ...' % len_diff,
                    text[-length/2:]])


def render_rss(rss_items):
    rss = ET.Element('rss', {'version': '2.0'})
    channel = ET.SubElement(rss, 'channel')
    title_elem = ET.SubElement(channel, 'title')
    title_elem.text = DEFAULT_TITLE
    desc_elem = ET.SubElement(channel, 'description')
    desc_elem.text = DEFAULT_DESC
    link_elem = ET.SubElement(channel, 'link')
    link_elem.text = DEFAULT_LINK

    for rss_item in rss_items:
        item = ET.SubElement(channel, 'item')
        for tag, text in rss_item._asdict().items():
            if tag in EXCLUDE_TAGS:
                continue
            if tag == 'link' and text is None:
                text = DEFAULT_LINK
            if tag == 'guid':
                text = GUID_URL_TMPL.format(guid=text)
                # elem = ET.SubElement(item, tag, {'isPermaLink': 'false'})
            elem = ET.SubElement(item, tag)
            elem.text = text

    return ET.tostring(rss, encoding='UTF-8')


def lastn_emails(mb,
                 n,
                 parser=DEFAULT_SUBJECT_PARSER,
                 delete=True):
    emails = []
    for key in reversed(mb.keys()):
        if parser.match(mb[key].get('subject')):
            if len(emails) < n:
                emails.append(mb[key])
            elif delete:
                del mb[key]

    return emails


def rss_from_emails(path, maximum, delete=True):
    with closing(mbox_readonlydir(path)) as mb:
        emails = lastn_emails(mb, maximum, delete=delete)
        rendered = render_rss([RSSItem.fromemail(email)
                               for email in emails])

    return rendered


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mbox')
    parser.add_argument('--output', '-o', default=None)
    parser.add_argument('--maximum', '-m', type=int, default=256)
    parser.add_argument('--save', '-s', default=False,
                        action='store_true')
    args = parser.parse_args()

    rendered = rss_from_emails(args.mbox,
                               args.maximum,
                               delete=not args.save)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(rendered)
    else:
        print rendered


if __name__ == '__main__':
    main()
