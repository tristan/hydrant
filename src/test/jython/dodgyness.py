from org.python.core import PyInstance

def _dodgy_cmp(self, o):
    print 'using dodgy_cmp!'
    values = []
    for i in [self, o]:
        if isinstance(i, PyInstance):
            if hasattr(i, "valueOf"):
                values.append(i.valueOf(i))
            else:
                raise Exception("""can't do that!""")
        else:
            values.append(i)
    return values[0].__cmp__(values[1])

def _dodgy_compare(f1, f2):
    print 'using _dodgy_compare!'
    if isinstance(f1, PyInstance):
        if hasattr(f1, "valueOf"):
            f1 = f1.valueOf(f1)
        else:
            raise Exception("""can't do that!""")
    if isinstance(f2, PyInstance):
        if hasattr(f2, "valueOf"):
            f2 = f2.valueOf(f2)
        else:
            raise Exception("""can't do that!""")
                
    if f1 < f2:
        return -1
    if f1 > f2:
        return 1
    return 0

def _dodgy_valueof(o):
    print 'dodgy valueOf!'
    return o.dodgy_valueOf(o)

def dumpStack():
    from java.lang import Thread
    fl = ['sun.reflect.NativeMethodAccessorImpl', 
          'java.lang.reflect.Method',
          'sun.reflect.DelegatingMethodAccessorImpl',
          'org.python.core.PyTableCode',
          'org.python.core.PyCode',
          'org.python.core.Py',
          'org.python.core.PyFunction',
          'org.python.core.PyInstance',
          'org.python.pycode._pyx0',
          'org.python.util.jython',
          'org.python.util.PythonInterpreter',
          'org.python.core.PyMethod',
          'org.python.core.PyObject',
          ]
    st = list(Thread.currentThread().getStackTrace())
    fst = [i for i in st if i.className not in fl]
    for i in fst:
        print '%s:%s' % (i.getFileName(), (i.getLineNumber() < 0) and 'Unknown' or i.getLineNumber())
    
def bedodgy():
    from java.lang import Float
    #Float.__dict__['dodgy_valueOf'] = Float.valueOf
    #Float.__dict__['valueOf'] = _dodgy_valueof
    floatMatches = ['Float.MAX_VALUE', 'Float.MIN_VALUE', 'Float.NEGATIVE_INFINITY', 'Float.NaN', 'Float.POSITIVE_INFINITY', 'Float.SIZE', 'Float.TYPE', 'Float.compare', 'Float.compareTo', 'Float.floatToIntBits', 'Float.floatToRawIntBits', 'Float.infinite', 'Float.intBitsToFloat', 'Float.isInfinite', 'Float.isNaN', 'Float.naN', 'Float.parseFloat', 'Float.toHexString', 'Float.toString', 'Float.valueOf', 'Float.__class__', 'Float.annotation', 'Float.anonymousClass', 'Float.array', 'Float.asSubclass', 'Float.canonicalName', 'Float.cast', 'Float.classLoader', 'Float.classes', 'Float.componentType', 'Float.constructors', 'Float.declaredClasses', 'Float.declaredConstructors', 'Float.declaredFields', 'Float.declaredMethods', 'Float.declaringClass', 'Float.desiredAssertionStatus', 'Float.enclosingClass', 'Float.enclosingConstructor', 'Float.enclosingMethod', 'Float.enum', 'Float.enumConstants', 'Float.fields', 'Float.forName', 'Float.genericInterfaces', 'Float.genericSuperclass', 'Float.getCanonicalName', 'Float.getClassLoader', 'Float.getClasses', 'Float.getComponentType', 'Float.getConstructor', 'Float.getConstructors', 'Float.getDeclaredClasses', 'Float.getDeclaredConstructor', 'Float.getDeclaredConstructors', 'Float.getDeclaredField', 'Float.getDeclaredFields', 'Float.getDeclaredMethod', 'Float.getDeclaredMethods', 'Float.getDeclaringClass', 'Float.getEnclosingClass', 'Float.getEnclosingConstructor', 'Float.getEnclosingMethod', 'Float.getEnumConstants', 'Float.getField', 'Float.getFields', 'Float.getGenericInterfaces', 'Float.getGenericSuperclass', 'Float.getInterfaces', 'Float.getMethod', 'Float.getMethods', 'Float.getModifiers', 'Float.getName', 'Float.getPackage', 'Float.getProtectionDomain', 'Float.getResource', 'Float.getResourceAsStream', 'Float.getSigners', 'Float.getSimpleName', 'Float.getSuperclass', 'Float.interface', 'Float.interfaces', 'Float.isAnnotation', 'Float.isAnonymousClass', 'Float.isArray', 'Float.isAssignableFrom', 'Float.isEnum', 'Float.isInstance', 'Float.isInterface', 'Float.isLocalClass', 'Float.isMemberClass', 'Float.isPrimitive', 'Float.isSynthetic', 'Float.localClass', 'Float.memberClass', 'Float.methods', 'Float.modifiers', 'Float.name', 'Float.newInstance', 'Float.package', 'Float.primitive', 'Float.protectionDomain', 'Float.signers', 'Float.simpleName', 'Float.superclass', 'Float.synthetic', 'Float.class', 'Float.equals', 'Float.getClass', 'Float.hashCode', 'Float.notify', 'Float.notifyAll', 'Float.toString', 'Float.wait', 'Float.getTypeParameters', 'Float.typeParameters', 'Float.annotations', 'Float.declaredAnnotations', 'Float.getAnnotation', 'Float.getAnnotations', 'Float.getDeclaredAnnotations', 'Float.isAnnotationPresent']
   
    #for i in floatMatches:
    #    print i[6:]
    
    import Dodgy
    Dodgy.__dict__['___dodgy___echo'] = Dodgy.__dict__['echo']
    Dodgy.__dict__['echo'] = wrapfn
    
def wrapfn(fn, *args):
    print 'wrapped'
    fn.__call__(*args)