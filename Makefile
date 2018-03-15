# Copyright (c) 2015-2018, Intel Corporation
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of Intel Corporation nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

USERNAME = "testuser"
PASSWORD = "P@ssw0rd"
ROLE = "admin"


test: install lint-light reset-db
	@$(call msg,"Starting Integrity Tests ...")
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

reset-db:
	@$(call msg,"Resetting database ...");
	docker exec -it platformlauncher_dashboard_1 node /app/admin resetDB;

	@$(call msg,"Adding a user for testing ...");
	docker exec -it platformlauncher_dashboard_1 node /app/admin addUser $(USERNAME) $(PASSWORD) $(ROLE);

enter-debug: .install
	cd samples && python enter_pdb.py;

define msg
	tput setaf 2 && \
	for i in $(shell seq 1 80 ); do echo -n "-"; done; echo "" && \
	echo -e "\t"$1 && \
	for i in $(shell seq 1 80 ); do echo -n "-"; done; echo "" && \
	tput sgr0
endef
