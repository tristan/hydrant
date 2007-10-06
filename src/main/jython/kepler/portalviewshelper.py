from workflow.cache import *
from django.http import Http404

def build_crumbs_from_path(model, path):
    p = path.split('/')
    crumbs = []
    if len(p) > 1:
        crumbs.append({'name': model.name, 'path': '%s/' % '/'.join(['..' for j in range(len(p)-1)])})
        q = p[1:]
        size = len(q)-1
        for i in range(size):
            crumbs.append({'name': q[i], 'path': '%s/' % '/'.join(['..' for j in range(size-i)])})
    return crumbs

def add_new_workflow(form):
    # get Workflow model manipulator
    model = models.get_model('kepler', 'Workflow')
    manipulator = model.AddManipulator()
    errors = manipulator.get_validation_errors(form)
    if errors:
        raise Http404(unicode(errors))
    manipulator.do_html2python(form)
    new_object = manipulator.save(form)
    print new_object.pk

def update_existing_workflow(form, id):
    # get Workflow model manipulator
    model = models.get_model('kepler', 'Workflow')
    manipulator = model.ChangeManipulator(id)

    # this is some crazyness to check the form for missing fields
    # and add the original value for those fields so that the
    # manipulator doesn't bork out
    for i in manipulator.follow:
        # get the field class matching the member name
        f = [j for j in manipulator.opts.fields if j.name == i]
        if f:
            f = f[0]
            # get the list of form fields and traverse thru them
            for j in f.get_manipulator_field_names(''):
                if j not in form.keys():
                    # check if there is a _ in the field name
                    s = j.split('%s_' % f.name)
                    if len(s) > 1:
                        # if there is, get the base member name
                        o = getattr(manipulator.original_object, f.name)
                        # then find if it has a member with the split
                        if hasattr(o, s[1]):
                            o = getattr(o, s[1])
                        else:
                            o = None
                    else:
                        if j != f.get_attname():
                            attname = f.get_attname()
                        else:
                            attname = j
                        o = getattr(manipulator.original_object, attname)
                    if o is not None:
                        if hasattr(o, '__call__'):
                            form[j] = unicode(o.__call__())
                        else:
                            form[j] = unicode(o)

    errors = manipulator.get_validation_errors(form)
    if errors:
        raise Http404(unicode(errors))
    manipulator.do_html2python(form)
    manipulator.save(form)
