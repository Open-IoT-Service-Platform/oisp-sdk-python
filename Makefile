USERNAME = "testuser"
PASSWORD = "P@ssw0rd"
ROLE = "admin"


test: install lint-light
	@$(call msg,"Resetting database ...")
	@docker exec -it openiotconnector_dashboard_1 node /app/admin resetDB

	@$(call msg,"Adding a user for testing ...")
	@docker exec -it openiotconnector_dashboard_1 node /app/admin addUser $(USERNAME) $(PASSWORD) $(ROLE)
	@$(call msg,"Starting unittests ...")
	python -m unittest

format-files: .install-deps
	@$(call msg,"Autoformatting .py files in iotkitclient ...");
	autopep8 iotkitclient/*.py --in-place
	docformatter --in-place iotkitclient/*.py

lint-light:
	@$(call msg,"Running linters (light) ...");
	pylint --disable=fixme --score=n iotkitclient
	pycodestyle iotkitclient
	pycodestyle test

lint:
	@$(call msg,"Running linters (full) ...");
	pylint iotkitclient --score=n
	pycodestyle iotkitclient
	pycodestyle test
	pydocstyle iotkitclient --add-ignore=D105

install: .install

.install: .install-deps  $(shell find iotkitclient -type f)
	@$(call msg,"Installing project ...");
	sudo python setup.py install
	@touch $@

.install-deps: requirements.txt
	@$(call msg,"Installing dependencies ...");
	sudo pip install -r requirements.txt
	@touch $@

define msg
	tput setaf 2 && \
	for i in $(shell seq 1 80 ); do echo -n "-"; done; echo "" && \
	echo -e "\t"$1 && \
	for i in $(shell seq 1 80 ); do echo -n "-"; done; echo "" && \
	tput sgr0
endef
