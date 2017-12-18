format:
	autopep8 iotkitclient/*.py --in-place && \
	docformatter --in-place iotkitclient/*.py

lint-light:
	pylint --disable=fixme iotkitclient && \
	pycodestyle iotkitclient

lint:
	pylint iotkitclient && \
	pycodestyle iotkitclient && \
	pydocstyle iotkitclient --add-ignore=D105
