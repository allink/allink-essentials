class FeincmsTemplateInheritanceMixin(object):
    def response_class(*args, **kwargs):
        return kwargs['template'], kwargs['context']
