def list_vendored_modules():
    from pkgutil import walk_packages
    import pkg_resources._vendor
    return ["pkg_resources._vendor.{1}".format(*x) for x in walk_packages(pkg_resources._vendor.__path__)]

hiddenimports = list_vendored_modules()
