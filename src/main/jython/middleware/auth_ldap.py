# Ldap authentication backend for Django. Users are authenticated against
# an ldap server and their django accounts (name, email) are maintained
# automatically.
#
# Configuration is done in settings.py, these are the available settings:
#
# # Where to find the ldap server (optional, default: ldap://localhost)
# AUTH_LDAP_HOST = 'ldap://ldap.kaarsemaker.net'
# # Which ldap groups to mirror in django (optional, default [])
# AUTH_LDAP_GROUPS = ('webadmins','ubuntu')
# # The users must be in any of these groups (optional, default [])
# AUTH_LDAP_FILTER_GROUPS = AUTH_LDAP_GROUPS
# # DN for binding to the server (optional, default anonymous bind)
# #AUTH_LDAP_BINDDN = "cn=admin,dc=kaarsemaker,dc=net"
# #AUTH_LDAP_BINDPW = "TheAdminPassword
# # Base DN for users and groups (required)
# AUTH_LDAP_BASEDN_USER = 'ou=People,dc=kaarsemaker,dc=net'
# AUTH_LDAP_BASEDN_GROUP = 'ou=Group,dc=kaarsemaker,dc=net'
# # Do we need to make the user staff?
# AUTH_LDAP_CREATE_STAFF = True
#
# # If you want LDAP to be your only authentication source, use
# AUTHENTICATION_BACKENDS = ('myproject.auth_ldap.LdapAuthBackend',)
# # If you want to use ldap and fall back to django, use
# AUTHENTICATION_BACKENDS = ('myproject.auth_ldap.LdapAuthBackend',
#                            'django.contrib.auth.backends.ModelBackend')
#
# When using ldap exclusively, the superuser created with ./manage.py 
# cannot log in unless the account also exists in ldap. So either make
# sure the user exists in ldap or give another user superuser rights
# before disabling the builtin authentication.
#
# Make sure all your ldap users have a mail attribute, otherwise this
# module will break.
#
# (c)2008 Dennis Kaarsemaker <dennis@kaarsemaker.net>
# License: Same as django

# converted for jython to use jldap
# used: http://www.blasum.net/holger/wri/comp/net/7appl/ldap/bochum2003/src/doc/api.txt
# to translate calls

from django.contrib.auth.models import User, Group
from django.contrib.auth.backends import ModelBackend
from django.conf import settings
from com.novell import ldap

def _find_dn(lc, username):
    ldapVersion = lc.LDAP_V3
    lc.bind(getattr(settings, 'AUTH_LDAP_BINDDN', ''),
              getattr(settings, 'AUTH_LDAP_BINDPW', ''))
    res = lc.search(settings.AUTH_LDAP_BASEDN_USER, lc.SCOPE_ONE,
                    "uid=" + username, [], False)
    if not res.hasMore():
        return None
    ent = res.next()
    dn = ent.getDN()
    attrs = {}
    for name, value in [(i.getName(), [j for j in i.getStringValues()]) for i in ent.getAttributeSet()]:
        attrs[name] = value
    return (dn, attrs)

def _find_groups(lc, dn):
    if not getattr(settings, 'AUTH_LDAP_GROUPS', None) and \
       not getattr(settings, 'AUTH_LDAP_FILTER_GROUPS', None):
        return []
    lc.bind(getattr(settings, 'AUTH_LDAP_BINDDN', ''),
              getattr(settings, 'AUTH_LDAP_BINDPW', ''))
    res = lc.search('ou=Organisation,ou=groups,dc=jcu,dc=edu,dc=au', lc.SCOPE_ONE,
                    "uniqueMember=" + dn, ['cn'], False)
    ret = []
    while res.hasMore():
        e = res.next()
        ret.append(e.getAttribute('cn').getStringValue())
    return ret
    #return [x[1]['cn'][0] for x in res]

class LdapAuthBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        # Authenticate against ldap
        #ls = ldap.initialize(getattr(settings, 'AUTH_LDAP_HOST', 'ldap://localhost'))
        ldapHost = getattr(settings, 'AUTH_LDAP_HOST', 'ldap://localhost')
        if ldapHost.startswith('ldap://'):
            ldapHost = ldapHost[7:]
        #TODO: get port from url
        if ldapHost.endswith('/'):
            ldapHost = ldapHost[:-1]

        lc = ldap.LDAPConnection()
        lc.connect(ldapHost, ldap.LDAPConnection.DEFAULT_PORT)
        dn, attrs = _find_dn(lc, username)
        if not dn:
            lc.disconnect()
            return None
        try:
            lc.bind(dn, password)
        except ldap.LDAPException:
            lc.disconnect()
            return None
        # Are we allowed to log in
        groups = _find_groups(lc, dn)
        if getattr(settings, 'AUTH_LDAP_FILTER_GROUPS', None):
            for group in getattr(settings,'AUTH_LDAP_FILTER_GROUPS',[]):
                if group in groups:
                    break
            else:
                lc.disconnect()
                return None

        # OK, we've authenticated. Do we exist?
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username, attrs['mail'][0], password)
            user.is_active = True
            if getattr(settings, 'AUTH_LDAP_BINDPW', False):
                user.is_staff = True
        user.first_name = attrs['givenName'][0]
        user.last_name = attrs['sn'][0]
        user.email = attrs['mail'][0]
        user.password = 'This is an LDAP account'

        # Group manglement
        for group in getattr(settings,'AUTH_LDAP_GROUPS',[]):
            dgroup, created = Group.objects.get_or_create(name=group)
            if created:
                dgroup.save()
            if dgroup in user.groups.all() and group not in groups:
                user.groups.remove(dgroup)
            if dgroup not in user.groups.all() and group in groups:
                user.groups.add(dgroup)

        # Done!
        user.save()
        lc.disconnect()
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
