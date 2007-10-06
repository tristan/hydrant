import sys
import java.lang.Exception
import java.lang.NoClassDefFoundError

def testimport(name):
    __import__(name)
    m = sys.modules[name]
    for i in range(2):
        try:
            return getattr(m, "__file__", None) or True
        except java.lang.NoClassDefFoundError, e:
            pass
        except java.lang.Exception, e:
            return e