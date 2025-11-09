import os

def read_cert_file(filename):
    cert_path = os.path.join(os.path.dirname(__file__), 'saml', filename)
    with open(cert_path, 'r') as f:
        return f.read()
    
app_url = os.getenv('APP_URL', 'http://rwauto.local:8080')

SAML_SETTINGS = {
    # If 'strict' is True, then the Python Toolkit will reject unsigned
    # or unencrypted messages if it expects them signed or encrypted
    'strict': False,
    
    # Enable debug mode (to print errors)
    'debug': True,
    
    # Service Provider Data
    'sp': {
        # Identifier of the SP entity (must be a URI)
        # get from env
        'entityId': app_url + '/saml/metadata',

        # Assertion Consumer Service info
        'assertionConsumerService': {
            # URL Location where the <Response> from the IdP will be returned
            'url': app_url + '/saml/acs',
            # SAML protocol binding to be used
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
        },
        
        # Single Logout Service info
        'singleLogoutService': {
            'url': app_url + '/saml/sls',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
        },
        
        # NameID format
        'NameIDFormat': 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
        
        # SP certificates (leave empty for now)
        'x509cert': read_cert_file('sp.crt'),
        'privateKey': read_cert_file('sp.key'),
    },
    
    # Identity Provider Data
    'idp': {
        # Identifier of the IdP entity
        'entityId': 'https://idp.n1.nassaucandy.com/',
        
        # SSO endpoint info
        'singleSignOnService': {
            'url': 'https://idp.n1.nassaucandy.com/module.php/saml/idp/singleSignOnService',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
        },
        
        # SLO endpoint info
        'singleLogoutService': {
            'url': 'https://idp.n1.nassaucandy.com/module.php/saml/idp/singleLogout',
            'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
        },
        
        # Public x509 certificate of the IdP
        'x509cert': '''MIIEnTCCAwWgAwIBAgIUeVlWV2WMGkrowHpqGfy4NL7pROwwDQYJKoZIhvcNAQEL
BQAwXjELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAk5ZMSEwHwYDVQQKDBhJbnRlcm5l
dCBXaWRnaXRzIFB0eSBMdGQxHzAdBgNVBAMMFmlkcC5uMS5uYXNzYXVjYW5keS5j
b20wHhcNMjQwODI4MDIyMDA1WhcNMzQwODI4MDIyMDA1WjBeMQswCQYDVQQGEwJV
UzELMAkGA1UECAwCTlkxITAfBgNVBAoMGEludGVybmV0IFdpZGdpdHMgUHR5IEx0
ZDEfMB0GA1UEAwwWaWRwLm4xLm5hc3NhdWNhbmR5LmNvbTCCAaIwDQYJKoZIhvcN
AQEBBQADggGPADCCAYoCggGBAMcYG1v8i+Ch36JFCb0QIN/x+vUqj8MZJlrTKqdc
MzKtHbmJ2oB64PrjKsM0faig3DJU3SdpBYn54d4pTJDlmy7FWc3N5EeeZZE+AyLr
1Z780Vc+P676/jB43z6YjuWR7aeuM0VSaSQae74e4G/Q+jDzm3PLkefQFqu1cI1V
T+oBPp7VxdJQkEqUsUDRLH4BDeSi5G4qPS53yJ4J16KdhJMTCmKoqQA1/0UEQZ/o
nCVUMo+yoZeas+2Db4oeEWrKvvfPJcOoA5zTdDL2bi6ZpMjVh5a+C/QCCM7Nmugk
+xPimD+AEKWoOhHz+U1v9mdwfdiIEmB5XJBrieEIG7KkeMNlg2npJn68JKkbVyWS
QFmHBZVPqoz4xfG6l/DDQWzibvHQN0Gan+ZhB6wmwwHVlNOL0tl5JrXwvSLhH7Fm
K7z2MEyIOybx1UvJDSKNY/F8MrfuBMkjSTly+RlcPWWetw4bk1orBMhCrv0P+psO
AuFtXaw0EYUjQZLxyR0iJaqeWQIDAQABo1MwUTAdBgNVHQ4EFgQUh1I6ghFrqo8Z
yV7EFs/qyqvdFRQwHwYDVR0jBBgwFoAUh1I6ghFrqo8ZyV7EFs/qyqvdFRQwDwYD
VR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAYEAK+Ht3I9OFwksxCjN0MY4
YG9ElPn4QsNj/C5EhgVc7s2nMbDsmapW6ldOthzxnYHVhT0ZxUma5+8vEJWdWc3n
UMPTPy0msViBhqzIp+iPAOeutdPmJpeEDcP6su3Fy+48ZkwXxBz6Jcuqcpz44Z6/
gmn4zKZBvyiWxW8dcNr20e6943i2G3ViVgIxODZ+a9EVkK8wvuArTFlAfAQTOiRs
cxh49hHycnyH+HmjhagMEzc9YJ+WxexhN1VnBdbgVSvyQMHx/NTnihYX5OkTzO8C
5hEPveMz8S0wPByBulyyFG1eXrGu1Yinb2JTcQRhVOV+XfwmBXSK91HSDw1aAe9W
uIrlEFj1ZWq0xkvSZ0f1oeiEplDulZSbnTsKiZKj8AUj6wqWL+f80mJUggvsz01U
y9B3Csxi8CMwnke+aRXjNs7Qfd3KSAZ4Vdf63JQlaT/GDpUNxT8PkiDDy9OlpKao
bafcq2gTHrg4+CWpzerz3zCj4jQxI9ZOvByimS2gMAtj''',
    },
}