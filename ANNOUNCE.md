# Cronfed: Minimum Viable Monitoring

Every project should be monitored. It’s common sense. We all know
it. We’re all _sensible_ developers. What is constructed must
eventually fall, and without monitoring, we won’t know when or how to
fix it.

And yet thousands of projects go without logging or monitoring,
working fine until they don’t, preventably depressing countless
others.

[**Cronfed**](https://github.com/hatnote/cronfed) is a Python package
that embodies a **Minimum Viable Monitoring **mindset. Something is
better than nothing, and there are far too many cron jobs with
nothing. Whether lazy or busy, take 5 minutes and clear your
conscience.

`pip install cronfed`

`echo ”*/15 * * * * /usr/bin/python -m cronfed --output /var/www/mysite/assets/cronfed.rss /var/mail/myuser 2>&1 | tee -a /home/myuser/project/logs/cronfed.txt<code>”`</code>

Just replace “myuser”, the “mysite” path, and the&nbsp;“logs” with the
appropriate paths and you’ll be ready to point your
[feedreader](http://theoldreader.com) or [IFTTT](https://ifttt.com/)
at your site and commence breathing easier. Learn more on [the Cronfed
docs](hatnote.github.io/cronfed/).

![simpsbird](https://31.media.tumblr.com/1ce65aa6920ac4f62c36790dab032342/tumblr_inline_nlhyytPLYW1ql4e1e.gif)

_If only all solutions were this easy and consequence-free._

We use [Cronfed](github.com/hatnote/cronfed) for Hatnote’s [Recent
Changes Map](rcmap.hatnote.com) and [Weeklypedia](weekly.hatnote.com)
(which just turned 1! [You should sign up](weekly.hatnote.com), learn
about Wikipedia, and experience the reliability firsthand!)
