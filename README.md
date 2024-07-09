# fia-api
The flexible interactive automation ReST API.  
![License: GPL-3.0](https://img.shields.io/github/license/fiaisis/run-detection)
![Build: passing](https://img.shields.io/github/actions/workflow/status/fiaisis/fia-api/tests.yml?branch=main)
[![codecov](https://codecov.io/gh/fiaisis/fia-api/branch/main/graph/badge.svg?token=XRJ1F7TEIT)](https://codecov.io/gh/fiaisis/fia-api)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/PyCQA/pylint)

## Local Install
`pip install .[all]`
You may need to escape the square brackets e.g. \[all\]

## Running Directly for development

### Env Vars
The required env vars to run are:
 - FIA_API_API_KEY - This sets the api key needed to use the specification endpoints
 - DB_USERNAME - the database username - default: postgres
 - DB_PASSWORD - The database password - default: password
 - DB_IP - The database host - default: localhost:5432
 - DEV_MODE - When true will disable auth - default: False

```shell
uvicorn fia_api.fia_api:app --reload  
```

The reload option will reload the api on code changes.

To run the API with no authentication for development, the DEV_MODE env var must be set to True


## How to container

Build using this command in the root of this repository:

```shell
docker build . -f ./container/fia_api.D -t ghcr.io/fiaisis/fia-api
```

Run on port 8080, by binding port 80 to port 8080 with a built container:
```shell
docker run -p 8080:80 ghcr.io/fiaisis/fia-api
```

How to push the container to the Github container registry:
```shell
docker push ghcr.io/fiaisis/fia-api -a
```

## API Documentation
Once deployed the auto generated api documentation is available at `/docs`. These can be used to inspect the API, and
can be used to try out each endpoint, which is useful for some manual testing and verification.

## Integration and end-to-end Testing
To run the integration and e2e tests, a postgres database is expected at localhost:5432 with user: postgres 
password:password

## Routers
The endpoint functions are in the `routers.py` module. If this module grows to an unmanageable size this can be split up
into a package and seperate `router` objects can be created with different rules such as path prefixes. More on this can
be found in the FastAPI documentation

## Exception Handlers
By default if an exception is not handled the API will return a 500 - internal server error. It is possible to define 
custom exception handlers to prevent 500 status codes for certain exceptions. These handlers are defined in the
`exception_handlers.py` module, and must be registered to the app in the `ir_api.py` module.


## Transforms Overview

Transforms are used to apply modifications to instrument scripts based on reduction input parameters. They enable you to
dynamically adapt the script depending on specific requirements, such as changing configuration settings, altering input
data, or modifying the processing flow.

### Adding New Transforms

To add a new transform for a different instrument, follow these steps:
  - Create a new class that inherits from the Transform abstract base class, and implement the apply method. This method
takes a PreScript object and a Reduction entity as arguments, and modifies the script as needed. 

For example:

```python
class YourInstrumentTransform(Transform):
    def apply(self, script: PreScript, reduction: Reduction) -> None:
        # Your script modification logic here e.g.
        script.script = f"print('hello {reduction.reduction_inputs.get('user', 'world')}')"
```
  - Update the get_transform_for_instrument factory function to return an instance of your new transform class when the 
appropriate instrument is provided as input by adding a new case for your instrument in the match statement:

```python
def get_transform_for_instrument(instrument: str) -> Transform:
    match instrument.lower():
        case "mari":
            return MariTransform()
        case "your_instrument":
            return YourInstrumentTransform()
        case _:
            raise MissingTransformError(f"No transform for instrument {instrument}")
```

## Data Access Pattern
The api is implementing a repository and specification pattern.
All queries are defined within specifications, basic ordering is available in the base specification module via a func
and a `@paginate` decorator is available to provide pagination to any specification.

## Database Generation Script for Development Environment
### Overview

This script is designed to generate a mock database for the development environment. It populates the database with 
random but realistic data related to a set of instruments and their associated runs, reductions, and scripts. This 
allows developers to easily simulate a real-world scenario, thereby making local development and testing more efficient 
and effective.

### How to Use
With a postgres database running, execute the script, navigate to the script’s directory and run it using Python:

`python db_generator.py`

### What the Script Does
When executed, the script performs the following actions:

1. Database Reset: It first clears the existing tables in the database, ensuring a clean slate.
2. Instrument Generation: Populates the database with a predefined list of instruments.
3. Data Generation: For each instrument, it generates:
   - Random runs with various attributes like start and end times, number of frames, experiment number, and associated users.
   - Reduction entries with various states, input parameters, and (optionally) output parameters.
   - Script entries with a SHA-1 hash and a simple script content.
   - Data Insertion: Inserts 10,000 of these randomly generated 'reduction' entries, each associated with random instrument entries, into the database.

### Note
The script is seeded with a constant seed value (in this case 1), which means that every time you run the script, 
it will generate the same random data. If you want different random data each time, you can remove or change the seed 
value.
