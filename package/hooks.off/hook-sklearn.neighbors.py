from PyInstaller.utils.hooks import collect_submodules, is_module_satisfies

hiddenimports = []

if is_module_satisfies("scikit_learn >= 0.22"):
    # 0.22 and later
    hiddenimports += [
        'sklearn.neighbors._typedefs',
        'sklearn.neighbors._quad_tree',
        'sklearn.neighbors._partition_nodes'
    ]
else:
    # 0.21
    hiddenimports += [
        'sklearn.neighbors.typedefs',
        'sklearn.neighbors.quad_tree',
    ]

# The following hidden import must be added here
# (as opposed to sklearn.tree)
hiddenimports += ['sklearn.tree._criterion']
