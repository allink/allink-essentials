Integrate Mailchimp
===================

Requirements
------------
* mailchimp

Settings
--------
* required:
    * MAILCHIMP_API_KEY
    * MAILCHIMP_LIST_ID

* optional:
    * MAILCHIMP_SIGNUP_FORM as 'my_app.forms.SignupForm'
    * MAILCHIMP_DOUBLE_OPTIN (default is False)
    * MAILCHIMP_SEND_WELCOME (default is False)

Form
----
If the SignupForm is customized it should inherit mailchimp_api.forms.SignupForm and its save function

Urls
----
Include mailchimp_api.urls in the main urls file.
<pre>url(r'^mailchimp/$', include('allink_essentials.mailchimp_api.urls')),</pre>

Template
--------
If default template isn't used, the app doesn't need to be registered.
