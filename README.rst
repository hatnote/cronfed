Cronfed
=======

Cronfed is a tool for monitoring basic batch jobs, or any other
cron-based scheduled commands. It achieves this by parsing a given
mailbox and turning it into an RSS feed, which can then be monitored
with your browser_, feedreader_ or other RSS-compatible service (such
as IFTTT_).

Simply add a cron job to generate the feed, pointing it at a
web-accessible location (such as a `public_html` directory or your
site's assets directory). Check out the example for some real-world
Cronfed usage, with an explanation of how cron and Cronfed work
together.

Cronfed is aimed at providing a basic threshold of monitoring without
complex automation or dependencies, making it suitable for smaller
projects which otherwise might go without any monitoring at all. It's
so easy to set up and use on the standard Linux/BSD machine that
there's no reason to not use it from Day 1. While Cronfed makes
attempts at limiting the amount of information externalized, it is not
recommended for jobs with extremely-sensitive information.

*"Cronfed: It's the least you could do!"*

Example
-------

First, let's look at a basic cron job. This one will fetch our data
once an hour, on the hour.

```
0 * * * * /usr/bin/python /home/myuser/project/fetch.py 2>&1 | tee -a /home/myuser/project/logs/fetch.txt
```

Notice how the output (`stdout` + `stderr`) is piped to a log file,
but using the `tee` command. This ensures that the output goes to the
file as well as `stdout`. `cron` captures that `stdout` and puts it
into an email, which then gets sent to the user who owns the job. This
usually means the email goes to `myuser@localhost`, which on many
distributions means that it is saved to `/var/mail/myuser`. Do note
that if the command generates no output, then `cron` **will not send
an email**, so it's a good idea to emit an error message.

Once we're sure that email is being delivered, we're halfway
there. Now we just need the actual Cronfed cronjob:

```
*/15 * * * * /usr/bin/python -m cronfed --output /var/www/mysite/assets/cronfed.rss /var/mail/myuser 2>&1 | tee -a /home/myuser/project/logs/cronfed.txt
```

In this example we have `cronfed` regenerating our feed every fifteen
minutes. This is a pretty quick process in most cases, so feel free to
make it more often. In this case, the output of cronfed itself is
monitored in exactly the same way as normal cron jobs, with a logfile
and email to `user@localhost`.

History
-------

Cronfed was created for `Hatnote`_ to monitor the periodic data refreshes
necessary to generate `The Weeklypedia`_.


.. _browser: https://www.mozilla.org/en-US/firefox/new/
.. _feedreader: https://theoldreader.com/
.. _IFTTT: https://ifttt.com/
.. _Hatnote: http://hatnote.com
.. _The Weeklypedia: http://weekly.hatnote.com

* Copyright: (c) 2015 by Mark Williams and Mahmoud Hashemi
* License: BSD, see LICENSE for more details.
