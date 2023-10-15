SHELL := /bin/bash

# Show help.
.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  test         	un all tests for all roles in the repository using molecule."
	@echo "  test-changed 	Run all tests for a roles which have been modified since the last commit using molecule."
	@echo "  lint         	Lint all roles in the repository using yamllint and ansible-lint."
	@echo "  update-molecule Overwrite all molecule.yml files in roles from the molecule.yml in the repository root."

# Define directive to run a molecule test for a role directory.
define molecule-test
	echo "Testing role: $${roledir}" ;\
	if [ -f $${roledir}/default/molecule.yml ]; then \
		echo "Found molecule.yml for role: $${roledir}" ;\
		pushd $$(dirname $${roledir}) ;\
		export INSTANCE_NAME=$$(echo "molecule-$$RANDOM") ;\
		molecule test ;\
		popd ;\
	else \
		echo "No molecule.yml found for role: $${roledir}" ;\
	fi
endef

# Run all tests for all roles in the repository using molecule.
.PHONY: test
test:
	@set -e ;\
	for roledir in roles/*/molecule; do \
		$(molecule-test) ;\
	done ;\
	echo "Success!"

# Run all tests for a roles which have been modified since the last commit using molecule.
.PHONY: test-changed
test-changed:
	@set -e ;\
	for roledir in $$(git diff --name-only HEAD HEAD~1 | grep roles | cut -d '/' -f 2 | uniq); do \
		$(molecule-test) ;\
	done ;\
	echo "Success!"

# Lint all roles in the repository using yamllint and ansible-lint.
.PHONY: lint
lint:
	@set -e ;\
	yamllint -d relaxed . ;\
	ansible-lint --profile safety -w var-naming[no-role-prefix] ;\
	echo "Success!"

# Overwrite all molecule.yml files in roles from the molecule.yml in the repository root.
.PHONY: update-molecule
update-molecule:
	@set -e ;\
	if [ ! -f molecule.yml ]; then \
		echo "ERROR: No molecule.yml found in repository root" ;\
		exit 1 ;\
	fi ;\
	for roledir in roles/*/molecule; do \
		echo "Updating molecule.yml for role: $${roledir}" ;\
		if [ ! -f $${roledir}/default/molecule.yml ]; then \
			echo "ERROR: No molecule.yml found for role: $${roledir}" ;\
			exit 1 ;\
		fi ;\
		if cmp -s molecule.yml $${roledir}/default/molecule.yml; then \
			echo "WARNING: $${roledir}/default/molecule.yml equals molecule.yml in repository root, skipping." ;\
		else \
			cp molecule.yml $${roledir}/default/molecule.yml ;\
		fi ;\
	done ;\
	echo "Success!"
