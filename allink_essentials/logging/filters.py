import logging
from django.http import UnreadablePostError


class SkipUnreadablePostError(logging.Filter):
    """
    use like shown in your logging configuration

    'filters': {
        'skip_unreadable_posts': {
            '()': 'allink_essentials.logging.filters.SkipUnreadablePostError',
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['skip_unreadable_posts'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    """

    def filter(self, record):
        if record.exc_info:
            exc_type, exc_value = record.exc_info[:2]
            if isinstance(exc_value, UnreadablePostError):
                return False
        return True
