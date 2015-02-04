from django.db import models


class SearchQuerySet(models.query.QuerySet):
    def __init__(self, model=None, fields=None, using=None, query=None):
         super(SearchQuerySet, self).__init__(model=model, using=using, query=query)
         self._search_fields = fields

    def search(self, query):

        meta = self.model._meta

        # Get the table name and column names from the model
        # in `table_name`.`column_name` style
        columns = [meta.get_field(name, many_to_many=False).column for name in self._search_fields]
        full_names = ["%s.%s" % (meta.db_table, column) for column in columns]

         # Create the MATCH...AGAINST expressions
        fulltext_columns = ", ".join(full_names)
        match_expr = ("MATCH(%s) AGAINST ('%s')" % (fulltext_columns, query))

         # Add the extra SELECT and WHERE options
        return self.extra(select={'relevance': match_expr},
                                where=[match_expr])


class SearchManager(models.Manager):
    def __init__(self, fields=None):
        super(SearchManager, self).__init__()
        self._search_fields = fields

    def get_query_set(self):
        if self._search_fields:
            return SearchQuerySet(model=self.model, fields=self._search_fields)
        else:
            return super(SearchManager, self).get_query_set()

    def search(self, query):
        return self.get_query_set().search(query)
