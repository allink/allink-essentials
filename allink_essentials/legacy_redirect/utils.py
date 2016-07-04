# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils import translation

from django.contrib.sites.models import Site
from importlib import import_module

_base_url = None


def choices_from_sitemaps():
    ''' Build up select choices
        from items declared in sitemaps

        - If we got a MPTT object (https://github.com/django-mptt/django-mptt)
        display indentation according to level
        - Display page language where we can get to it
        - Handle i18n sitemaps correctly
    '''
    url_mod = import_module(settings.ROOT_URLCONF)
    sitemaps = url_mod.sitemaps

    def label_from_instance(instance, lang=None):
        if hasattr(instance, '_mptt_meta'):
            # we got a tree object (e.g. FeinCMS page)
            level = getattr(instance, instance._mptt_meta.level_attr)
        else:
            # fallback, no different levels
            level = 0

        name = instance.__unicode__()
        if level:
            level_indicator = '---' * level
            name = u'%s %s' % (level_indicator, name)

        if lang:
            name = u'%s (%s)' % (name, lang)
        elif hasattr(instance, 'language'):
            name = u'%s (%s)' % (name, getattr(instance, 'language'))
        return name

    def _urls(item, smap):
        # copied from django.contrib.sitemaps.get_urls()
        # cycle trough all languages for i18n sensitive
        # sitemaps
        if getattr(smap, 'i18n', False):
            out = []
            current_lang_code = translation.get_language()
            for lang_code, lang_name in settings.LANGUAGES:
                translation.activate(lang_code)
                out += [(item.get_absolute_url(), label_from_instance(item, lang=lang_code))]
            translation.activate(current_lang_code)
        else:
            out = [(item.get_absolute_url(), label_from_instance(item))]
        return out

    urls = [(None, '----------')]
    for name, smap in sitemaps.iteritems():
        if callable(smap):
            urls += [(None, '')]
            urls += [(None, name.upper())]
            urls += [(None, '----------')]
            smap = smap()
            for item in smap.items():
                urls += _urls(item, smap)
    return urls


def base_url():
    global _base_url
    if not '_base_url' not in locals() or not _base_url:
        _base_url = 'http://' + Site.objects.get_current().domain
    return _base_url
