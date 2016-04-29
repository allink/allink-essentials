# Legacy Redirect

## Requirements
* django-import-export==0.4.5

## Project settings
In settings/default.py add Middleware

```python
MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'allink_essentials.legacy_redirect.middleware.LegacyRedirectMiddleware',
    .
    .
    .
]
```

and App

```python
INSTALLED_APPS = [
    .
    .
    .
    'allink_essentials.legacy_redirect',
    'import_export',
]
```
