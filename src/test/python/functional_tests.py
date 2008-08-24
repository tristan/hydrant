import mechanize

br = mechanize.Browser()
br.open('http://localhost:8000/hydrant/')
#log in
br.follow_link(text='Log in')
br.select_form(name='login-form')
br['username'] = 'test'
br['password'] = 'testpw'
br.submit()
assert(br.find_link(text='Log out'))

#upload a workflow
br.follow_link(text='(upload new)')
br.select_form(name='upload-workflow-form')
br['name'] = 'Hello World!'
wf_file = file('/home/tristan/projects/svn/kepler-svn/demos/getting-started/04-HelloWorld.xml')
br.form.add_file(wf_file, filename='04-HelloWorld.xml', name='moml_file')
br['description'] = 'A very simple hello world demo workflow'
#br['public'] = ['ON']
