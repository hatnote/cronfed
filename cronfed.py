
# Credit to Mark Williams for this
import re
import sys
import socket
import hashlib
import argparse
import datetime
from contextlib import closing
from collections import namedtuple
import xml.etree.cElementTree as ET

from boltons.tzutils import UTC
from boltons.mboxutils import mbox_readonlydir

GENERATOR_TEXT = 'cronfed v1.0'

DEFAULT_LINK = 'http://github.com/hatnote/cronfed'
DEFAULT_DESC = 'Fresh cron output from cronfed'
DEFAULT_TITLE = 'Cronfed on %s' % socket.gethostname()
DEFAULT_GUID_URL_TMPL = None
# NOTE: would've used isPermalink=false but IFTTT does not like that

DEFAULT_EXCERPT = 16
DEFAULT_EXCLUDE_EXC = False
DEFAULT_SAVE = sys.maxint


DEFAULT_SUBJECT_RE = re.compile(
    'Cron <(?P<user>[^@].+)@(?P<host>[^>].+)> (?P<command>.*)')
DEFAULT_SUBJECT_TMPL = 'Cron: <%(user)s@%(host)s> %(command)s'
MESSAGE_ID_RE = re.compile('<(?P<id>[^@]+)@(?P<host>[^>+]+)>')


def find_python_error_type(text):
    from boltons.tbutils import ParsedTB
    try:
        tb_str = text[text.index('Traceback (most recent'):]
    except ValueError:
        raise ValueError('no traceback found')
    parsed_tb = ParsedTB.from_string(tb_str)
    return parsed_tb.exc_type


class CronFeeder(object):
    def __init__(self, mailbox_path, **kwargs):
        self.mailbox_path = mailbox_path
        self.output_path = kwargs.pop('output_path', None)
        self.save_count = kwargs.pop('save_count', DEFAULT_SAVE)
        self.feed_title = kwargs.pop('feed_title', DEFAULT_TITLE)
        self.feed_desc = kwargs.pop('feed_desc', DEFAULT_DESC)
        self.feed_link = kwargs.pop('feed_link', DEFAULT_LINK)
        self.guid_url_tmpl = kwargs.pop('guid_url_tmpl', DEFAULT_GUID_URL_TMPL)
        if not self.guid_url_tmpl:
            self.guid_url_tmpl = self.feed_link + '/{guid}'

        self.subject_re = kwargs.pop('subject_re', DEFAULT_SUBJECT_RE)
        self.subject_tmpl = kwargs.pop('subject_tmpl', DEFAULT_SUBJECT_TMPL)

        self.excerpt_len = kwargs.pop('excerpt_len', DEFAULT_EXCERPT)
        self.exclude_exc = kwargs.pop('exclude_exc', DEFAULT_EXCLUDE_EXC)
        if kwargs:
            raise TypeError('unexpected keyword arguments: %r' % kwargs.keys())

    def process(self):
        with closing(mbox_readonlydir(self.mailbox_path)) as mbox:
            emails = self._process_emails(mbox)
            rss_items = []
            for email in emails:
                rss_items.append(RSSItem.from_email(email,
                                                    parser=self.subject_re,
                                                    renderer=self.subject_tmpl,
                                                    excerpt=self.excerpt_len))
            rendered = self._render_feed(rss_items)

        if self.output_path:
            with open(self.output_path, 'w') as f:
                f.write(rendered)
        else:
            print rendered
        return

    def _process_emails(self, mbox):
        ret = []
        for key, email in reversed(mbox.items()):
            if self.subject_re.match(email.get('subject')):
                if len(ret) < self.save_count:
                    ret.append(email)
                else:
                    del mbox[key]
        return ret

    def _render_feed(self, rss_items):
        rss = ET.Element('rss', {'version': '2.0'})
        channel = ET.SubElement(rss, 'channel')
        title_elem = ET.SubElement(channel, 'title')
        title_elem.text = self.feed_title
        desc_elem = ET.SubElement(channel, 'description')
        desc_elem.text = self.feed_desc
        link_elem = ET.SubElement(channel, 'link')
        link_elem.text = self.feed_link

        gen_elem = ET.SubElement(channel, 'generator')
        gen_elem.text = GENERATOR_TEXT

        lbd_elem = ET.SubElement(channel, 'lastBuildDate')
        _now = datetime.datetime.now(tz=UTC)
        lbd_elem.text = _now.strftime('%a, %d %b %Y %H:%M:%S %z')

        for rss_item in rss_items:
            item = ET.SubElement(channel, 'item')
            for tag, text in rss_item._asdict().items():
                if tag == 'link' and text is None:
                    text = self.feed_link  # TODO: make this configurable?
                elif tag == 'guid':
                    text = self.guid_url_tmpl.format(guid=text)
                elem = ET.SubElement(item, tag)
                elem.text = text
        return ET.tostring(rss, encoding='UTF-8')

    @staticmethod
    def get_argparser():
        prs = argparse.ArgumentParser()
        add_arg = prs.add_argument
        add_arg('mailbox_path',
                help='path to the mailbox file to process for cron output')
        add_arg('--output', '-o', default=None,
                help='where to write the output, defaults to stdout')
        add_arg('--save', default=DEFAULT_SAVE, type=int,
                help='the number of cron emails to save, defaults to'
                ' saving all of them')
        add_arg('--title', default=DEFAULT_TITLE,
                help='top-level title for the RSS feed')
        add_arg('--desc', default=DEFAULT_DESC,
                help='top-level description for the RSS feed')
        add_arg('--link', default=DEFAULT_LINK,
                help='top-level home page URL for the RSS feed')

        add_arg('--exclude-exc', default=DEFAULT_EXCLUDE_EXC,
                action='store_true', help='whether to search for and include'
                ' Python exception types in the feed')
        add_arg('--excerpt', default=DEFAULT_EXCERPT, type=int,
                help='how much cron job output to include, defaults to a small'
                ' amount, specify 0 to disable excerpting')
        add_arg('--guid-url-tmpl', default=DEFAULT_GUID_URL_TMPL,
                help='template used to generate individual item links')
        return prs

    @classmethod
    def from_args(cls):
        kwarg_map = {'save': 'save_count',
                     'output': 'output_path',
                     'excerpt': 'excerpt_len',
                     'title': 'feed_title',
                     'desc': 'feed_desc',
                     'link': 'feed_link'}
        prs = cls.get_argparser()
        kwargs = dict(prs.parse_args()._get_kwargs())
        for src, dest in kwarg_map.items():
            kwargs[dest] = kwargs.pop(src)
        return cls(**kwargs)


BaseRSSItem = namedtuple('RSSItem', ['title', 'description', 'link',
                                     'pubDate', 'guid'])


class RSSItem(BaseRSSItem):
    @classmethod
    def from_email(cls, email,
                   parser=DEFAULT_SUBJECT_RE,
                   renderer=DEFAULT_SUBJECT_TMPL,
                   excerpt=DEFAULT_EXCERPT):
        body = email.get_payload()
        date = email['date']
        subject = email['subject']

        match = parser.match(subject)
        if not match:
            raise ValueError("Unparseable subject")  # TODO: handle this better
        subject_dict = match.groupdict()
        title = renderer % subject_dict

        match = MESSAGE_ID_RE.match(email.get('message-id', ''))
        if match:
            guid = match.group('id')
        else:
            guid = hashlib.sha224(date + subject + body).hexdigest()

        desc = 'At %s, Cron ran:\n\n\t%s' % (date, subject_dict['command'])
        try:
            python_error_type = find_python_error_type(body)
        except:
            python_error_type = None
        if python_error_type:
            desc += '\n\nPython exception: %s.' % python_error_type

        if body:
            desc += '\n\nCommand output:\n\n\t' + summarize(body, excerpt)

        return cls(title=title, description=desc, link=None,
                   pubDate=date, guid=guid)


def summarize(text, length):
    """
    Length is the amount of text to show. It doesn't include the
    length that the summarization adds back in."
    """
    len_diff = len(text) - length
    if len_diff <= 0:
        return text
    elif not length:
        return '(%s bytes)' % len(text)
    return ''.join([text[:length/2],
                    '... (%s bytes) ...' % len_diff,
                    text[-length/2:]])


def main():
    cronfeeder = CronFeeder.from_args()
    cronfeeder.process()


if __name__ == '__main__':
    main()
