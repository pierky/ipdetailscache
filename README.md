ipdetailscache
==============

A Python library to gather IP address details (ASN, prefix, resource holder, reverse DNS) using the RIPEStat API, with a basic cache to avoid flood of requests and to enhance performances.

Usage
-----

Import the library, then setup a cache object and use it to gather IP address details.
The cache object will automatically load and save data to the local cache files.

Optionally, the cache object may be instantiated with the following arguments:
- IP_ADDRESSES_CACHE_FILE, path to the file where IP addresses cache will be stored (default: "ip_addr.cache");
- IP_PREFIXES_CACHE_FILE, path to the file where IP prefixes cache will be stored (default: "ip_pref.cache");
- MAX_CACHE, expiration time for cache entries, in seconds (default: 604800, 1 week);
- Debug, set to True to enable some debug messages (default: False).

Results are given in a dictionary containing the following keys: ASN, Holder, Prefix, HostName, TS (time stamp).

Hostname is obtained using the local socket.getfqdn function.

    import ipdetailscache
    cache = ipdetailscache.IPDetailsCache( IP_ADDRESSES_CACHE_FILE = "ip_addr.cache", IP_PREFIXES_CACHE_FILE = "ip_pref.cache", MAX_CACHE = 604800, Debug = False );
    result = cache.GetIPInformation( "IP_ADDRESS" )

Example
-------

    :~# python
    Python 2.7.2+ (default, Jul 20 2012, 22:15:08)
    [GCC 4.6.1] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import ipdetailscache
    >>> cache = ipdetailscache.IPDetailsCache();
    >>> result = cache.GetIPInformation( "193.0.6.139" )
    >>> result
    {u'Prefix': u'193.0.0.0/21', u'HostName': u'www.ripe.net', u'Holder': u'RIPE-NCC-AS Reseaux IP Europeens Network Coordination Centre (RIPE NCC),NL', u'TS': 140178124$

Requirements / Third-party Libraries
------------------------------------

Part of this work is based on Google Python IP address manipulation library (https://code.google.com/p/ipaddr-py/). You can install it using pip: `pip install ipaddr`.

Have a bug? Please create an issue here on GitHub at https://github.com/pierky/ipdetailscache/issues

Author
------

Pier Carlo Chiodi - http://pierky.com/aboutme

Blog: http://blog.pierky.com Twitter: <a href="http://twitter.com/pierky">@pierky</a>
