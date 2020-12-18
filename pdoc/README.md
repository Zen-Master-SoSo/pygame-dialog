# pdoc templates

This folder contains the config template used when creating html documentation using [pdoc](https://github.com/pdoc3/pdoc). Primarily, it turns off source code embedding.

To recreate the docs as they are, run the following command from the pygame_dialog project folder:

	$ pdoc3 --html --force --template-dir=pdoc --output-dir=docs pygame_dialog

In order to run the above command, you'll need pdoc3 and pygame_dialog both installed on your system, or at least "reachable" in the python syspath.

If you want to include the source code in the documentation, eliminate the "--template-dir" option:

	$ pdoc3 --html --force --output-dir=docs pygame_dialog

