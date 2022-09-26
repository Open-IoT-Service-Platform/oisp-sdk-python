# OISP Python SDK
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FOpen-IoT-Service-Platform%2Foisp-sdk-python.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FOpen-IoT-Service-Platform%2Foisp-sdk-python?ref=badge_shield)

=================================
This library provides Python bindings to the [Open IoT Service Platform (OISP)](https://github.com/Open-IoT-Service-Platform).

## Installation

---
**Note**
In order to experiment and test more easily, it is recommended to install OISP locally.
You can follow [these instructions](https://github.com/Open-IoT-Service-Platform/platform-launcher) to get going easily.

---

If you only want to use the SDK, just run:
```
pip install oisp
```

### For SDK development

If you want to develop the SDK, install using the git repository instead.

1. Clone the oisp-sdk-python repository from GitHub
2. Install the library:

``` bash
cd oisp-sdk-python
make install
```

## Getting started

### Creating a user
Assuming you have OISP running locally, open your browser and visit `localhost`. You can create a new user using the sign up button in the top right corner.

It is possible to create a user using the REST API as well, but you will still have to check you e-mail to activate the user. The methods for retrieving users are defined in the `Client` class.

### Client
Connection to the host is managed by the `Client` class. You need the URL for the API to create an instance.

``` python
import oisp
client = oisp.Client(api_root="http://localhost/v1/api/")
```

If you are connecting over proxies, you can specify those using the `proxies` parameter, see method documentation for `__init__` for details.

### Authentication

OISP offer couple of different authentication mechanism for different purposes. In order to manage accounts and devices you need to authenticate as a user. We will have a look at alternative strategies later.

``` python
client.auth("username", "password")
```

Once you log in using the auth method, you receive a token that is valid for one hour and will automatically be included in the requests made by the client object. You will get an `AuthenticationError` the first time you try to make a request after the token expires and need to reauth using the same method.

### Accounts
A User represents a person interacting with the system, wheres an Account is an organizational unit. An account can be managed by multiple users with different roles, and a user can manage multiple accounts.

Accounts are used to manage devices, component types etc.

You can create a new account simply by specifying its name. Please be aware that account names are not necessarily unique. **After creating a new account, you will need to reauth to refresh your token.**
``` python
account = client.create_account("test_account")
client.auth("username", "password")
```

In order to get a list of accounts that are managed by the user logged in, use the following method>
``` python
accounts = client.get_accounts()
```

### Devices
A devices represents an IoT Endpoint. As devices are managed by accounts, a device is created by the following method:
``` python
new_device = account.create_device("device_id", "device_name")
```
Device id has to be globally unique. We recommend using the MAC adress for the device. Device name does not have to be unique.

---
Functionality regarding a specific device is implemented in `Device` class (for example sending data, activation, deleting a device), functionality regarding all devices that belong to an account (data search, device creation etc) are implemented in the `Account` class.

---

Before sending data, a device needs to be activated. Activation returns a device token, which can be used for simple operations like sending data. This is the preferred way for requests that do not need priviliges, so save the returned device token. A device token can be updated by activating the device again.
``` python
device_token = device.activate()
```

You can retrieve a previously activated device directly from the client using the device token and device id. Note that the following method does not require you to auth before.
``` python
device = client.get_device(device_token, device_id)
```

### Submitting Data
A device can provide multiple datasets, which are organized in 'components'. Every component has a type and a name. For this example we will use a predefined component type but you can also create your own.

---
Component types catalog belongs to an account and can be managed using the `get_component_types_catalog`, `create_component_type`, `get_component_type` and other similar methods provided by the `Account` class. See respective method descriptions for details.

---
We add a component to a device by specifying the name and the the type. This returns a json dictionary representing the newly created component and contains the component id, which is used to add data to the component.
``` python
response = device.add_component("test_temperature_component", "temperature.v1.0")
cid = response["cid"]
```
You can access the existing components of a device with `device.components`.

In order to add data, use the `add_sample` method of a device (this does not submit the data to the service yet):
``` python
device.add_sample(cid, value_1)
device.add_sample(cid, value_2)
```
You can use the `on` and `loc` parameters if you want to include the time and location in which the data was sampled. If ommited `on` will be set to current time and `loc` will be left blank.

Once you want to submit and save your data, call the following method:
``` python
device.submit_data()
```
Seperation of adding samples and submisson allows you to add datapoints as you collect the input from sensors, but save on requests by submitting multiple values at once.

### Searching for data
You need to build a query to search for data that belongs to an account. The structure of the query is described in the API documentation ( [here if OISP is running locally](http://localhost/ui/public/api.html) ) and you can use a json style dictionary for your query.

However, it is more convenient to use the `DataQuery` class. A query created without any parameters will return all data submitted so far. For details on query parameters see the documentation on this class.

``` python
query = oisp.DataQuery()
response = account.search_data(query)
```

`response` is of type `QueryResponse` and `response.samples` array contains `Sample` objects which store data, location, time and device information.

``` python
# See all data values from the response
data_values = [sample.value for sample in response.samples]
```

## License
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FOpen-IoT-Service-Platform%2Foisp-sdk-python.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FOpen-IoT-Service-Platform%2Foisp-sdk-python?ref=badge_shield)
