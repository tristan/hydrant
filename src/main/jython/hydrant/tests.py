"""
>>> from django.contrib.auth.models import User
>>> u = User(username='test')
>>> u.set_password('test')
>>> u.save()
>>> u.pk
3L
>>> from django.test.client import Client
>>> c = Client()
>>> c.get('/portal/').status_code
200
>>> res = c.get('/portal/upload/')
>>> res.status_code
302
>>> c.login(username='test',password='wrong')
False
>>> c.login(username='test',password='test')
True
>>> res = c.get('/portal/upload/')
>>> res.status_code
200
>>> from django.utils.datastructures import FileDict
>>> file = open('/home/tristan/workspace/kepler/workflows/demo/simple_addition.xml')
>>> res = c.post('/portal/upload/', {'uri': '', 'public': 'on', 'uri_file': file})
>>> res.status_code
302
>>> from kepler.models import Workflow
>>> Workflow.objects.all()
[<Workflow: simple_addition>]
>>> w = Workflow.objects.all()[0]
>>> w.pk
1
>>> res = c.get('/portal/wf/%s/' % w.pk)
>>> res.status_code
200
"""
