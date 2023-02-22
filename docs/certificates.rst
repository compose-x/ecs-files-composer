
.. meta::
    :description: Files Composer features
    :keywords: AWS, Kubernetes, SSL, certificates


.. _certificates

===================
SSL Certificates
===================

Self signed certificates
============================

When deploying services, it is best practice where possible to enable TLS termination. Even when the certificates are
self-signed, this improves security dramatically. With the files composer, you can request to generate certificates on
the fly to later use with your application. This will create a private key and public certificate.

Below are optional properties and there default values that you can set so that the certificate information reflects
your needs.

+----------------------+---------------------------------------------+
| Property Name        | Default Value                               |
+======================+=============================================+
| emailAddress         | files-composer@compose-x.tld                |
+----------------------+---------------------------------------------+
| commonName           | the hostname retrieved from the os.hostname |
+----------------------+---------------------------------------------+
| countryName          | ZZ                                          |
+----------------------+---------------------------------------------+
| localityName         | Anywhere                                    |
+----------------------+---------------------------------------------+
| stateOrProvinceName  | Shire                                       |
+----------------------+---------------------------------------------+
| organizationName     | NoOne                                       |
+----------------------+---------------------------------------------+
| organizationUnitName | Automation                                  |
+----------------------+---------------------------------------------+
| validityEndInSeconds | 3*31*24*60*60=3Months                       |
+----------------------+---------------------------------------------+

.. note::

    The certificates are created once, and not automatically renewed after ``validityEndInSeconds`` expires.
    This is meant to be a solution to provision temporary certificates.

    There is no CA created and retrievable in this process.

jksConfig
------------

This is a configuration option that allows you to create a java key store (JKS) in the JKS format from the generated
certificate files. You can specify the fileName which will be created in the same folder, alongside the key and certificate.
You must specify a passphrase, which is used for both the private key and the jks encryption.


.. code-block::

    certificates:
      x509:
        /tmp/testing:
          keyFileName: nginx.key
          certFileName: nginx.crt
          commonName: test.net
          jksConfig:
            fileName: test.jks
            passphrase: somesecretpassword
