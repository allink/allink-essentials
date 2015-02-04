Such über SQL FULLTEXTINDEX
===========================

Beispiel
--------

<pre>
    from django.db import models
    from allink_essentials.search.utils import SearchManager

    class Article(models.Model):
         posted_date = models.DateField(db_index=True)
         title = models.CharField(maxlength=100)
         text = models.TextField()

         # Use a SearchManager for retrieving objects,
         # and tell it which fields to search.
         objects = SearchManager(fields=('title', 'text'))

         def __unicode__(self):
             return "%s (%s)" % (self.title, self.posted_date)
</pre>

Diese muss von Hand ausgeführt werden. Bei Projekten die Django-Migrationen benutzen kann eine Migration
erstellt werden mit RUN_SQL (https://docs.djangoproject.com/en/1.7/ref/migration-operations/#runsql)
<pre>
    CREATE FULLTEXT INDEX fulltext_article_title_text ON fulltext_article (title, text);
</pre>

<pre>
    >>> # Find articles about frameworks:
    >>> Article.objects.search('framework')

    [<Article: Introducing Django (2006-07-17)>,
    <Article: Django on Windows HOWTO (2006-04-03)>,
    <Article: Django for non-programmers (2006-05-02)>]
</pre>
