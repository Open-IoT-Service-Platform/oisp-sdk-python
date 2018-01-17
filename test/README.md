# Tests

## How to run tests

First make sure you have a running instance of oisp on localhost. See platform-launcher repository [here](https://github.com/Open-IoT-Service-Platform) repository.

To run tests:
``` bash
make test
```

This will install the package, run some linters with lighter settings and integrity tests. You may want to create and activate a python virtual environment to avoid dependency conflicts with your system.

This is the minimum standard for development code. For code to be merged in `master`, `make lint` should also succeed, which enforces more strict control.
