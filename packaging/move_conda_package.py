import shutil
from conda_build.api import get_output_file_paths  # @UnresolvedImport

binary_package_paths = get_output_file_paths("packaging/conda_recipes/cytoflow")

for p in binary_package_paths:
    shutil.move(p, 'dist/')