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

# PROJECT_NAME is used to find the containers, this should match
# COMPOSE_PROJECT_NAME in platform-launcher
NAMESPACE?=oisp
DASHBOARD_POD:=$(shell kubectl -n $(NAMESPACE) get pods -o custom-columns=:metadata.name | grep dashboard | head -n 1)

PROJECT_NAME ?= "oisp"
USERNAME = "testuser"
PASSWORD = "P@ssw0rd"
ROLE = "admin"


test: lint-light reset-db
	@$(call msg,"Starting Integrity Tests ...")
	virtualenv venv_test;
	. venv_test/bin/activate && \
	coverage run --source oisp setup.py test && \
	coverage report -m;

format-files: .install-deps
	@$(call msg,"Autoformatting .py files in oisp ...");
	autopep8 oisp/*.py --in-place
	docformatter --in-place oisp/*.py

lint-light:
	@$(call msg,"Running linters (light) ...");
	pylint --disable=fixme --score=n oisp
	pycodestyle oisp
	pycodestyle test

lint:
	@$(call msg,"Running linters (full) ...");
	pylint oisp --score=n
	pycodestyle oisp
	pycodestyle test
	pydocstyle oisp --add-ignore=D105

install: .install

.install: $(shell find oisp -type f)
	@$(call msg,"Installing project ...");
	sudo python setup.py install --force
	@touch $@

reset-db:
	@$(call msg,"Resetting database ...");
	kubectl -n $(NAMESPACE) exec -it $(DASHBOARD_POD) -c dashboard -- node /app/admin resetDB;

enter-debug: .install
	cd samples && python enter_pdb.py;

define msg
	tput setaf 2 && \
	for i in $(shell seq 1 80 ); do echo -n "-"; done; echo "" && \
	echo -e "\t"$1 && \
	for i in $(shell seq 1 80 ); do echo -n "-"; done; echo "" && \
	tput sgr0
endef
