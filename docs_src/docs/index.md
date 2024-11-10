# Welcome to the Hyrrokkin documentation

## Introduction

### Topology

Hyrrokkin is a library which manages the execution of computational graphs, which are termed topologies.  

Each topology consists of executable components called nodes.  

### Nodes, Ports and Links

Nodes are associated with a class which implements the node's behaviour, most notably the class will implement a `run` method which transforms a set of values received through that node's input ports into a set of values sent out via the node's output ports. 

A topology will also contain links, which connect the output port of one node to the input port of another.

### Packages and Package Configurations

Each node in a topology is an instance of a particular node type which defines the class which implements the node's functionality, and the names and Link Types of each input and output port associated with that node.  An output port of one node can only be connected to an input port of another node can only be connected by a link if they share the same Link Type.

Node types and link types are bundled together into a Package containing related functionality. 

A package may also define a package configuration which can be accessed by all nodes.    

### An Example Package

Consider a simple example package:

* NumberInputNode

Stores and outputs an integer value via its output port `data_out`, allowing this nuber to be updated by clients 

* PrimeFactorsNode

Expects numeric input values via its input port `data_in`, computes a list of its prime factors which are output via port `data_out`.

* NumberDisplayNode

Receives a list of numbers via its input ports `integer_data_in` amd `integerlist_data_in`, and communicates those to clients 

### Package Schema

Each package can define a configuration class - all node instances within a topology that belong to the package.

Each Package, and the Link Types, Node Types it contains, is specified in a JSON formatted document that represents the schema of that Package.  

```json
{
    "id": "numberstream",
    "metadata": {
        "name": "Number Stream",
        "version": "0.0.1",
        "description": "a small example package for manipulating numbers"
    },
    "configuration": {
        "classname": "numberstream_configuration.NumberstreamConfiguration"
    },
    "node_types": {
        "number_input_node": {
            "metadata": {
                "name": "Number Input Node",
                "description": "Define an integer value"
            },
            "output_ports": {
                "data_out": {
                    "link_type": "numberstream:integer"
                }
            },
            "classname": "nodes.number_input_node.NumberInputNode"
        },
        "prime_factors_node": {
            "metadata": {
                "name": "Prime Factors Node",
                "description": "Calculate the prime factors of each input number"
            },
            "input_ports": {
                "data_in": {
                    "link_type": "numberstream:integer",
                    "allow_multiple_connections": false
                }
            },
            "output_ports": {
                "data_out": {
                    "link_type": "numberstream:integerlist"
                }
            },
            "classname": "nodes.prime_factors_node.PrimeFactorsNode"
        },
        "number_display_node": {
            "metadata": {
                "name": "Number Display Node",
                "description": "Display all input numbers"
            },
            "input_ports": {
                "integer_data_in": {
                    "link_type": "numberstream:integer"
                },
                "integerlist_data_in": {
                    "link_type": "numberstream:integerlist"
                }
            },
            "output_ports": {
            },
            "classname": "nodes.number_display_node.NumberDisplayNode"
        }
    },
    "link_types": {
        "integer": {
            "metadata": {
                "name": "Integer",
                "description": "This type of link carries integer values"
            }
        },
        "integerlist": {
            "metadata": {
                "name": "IntegerList",
                "description": "This type of link carries values that are lists of integers"
            }
        }
    }
}
```

When refering to a link type, the package id should be used as a prefix, `<package-id>:<link-type-id>`.  In this example, `numberstream:integer` refers to the link type `number` defined in the `numberstream` example package.  This allows packages to refer to link types defined in other packages when defining nodes.

Each Node Type is associated with the following information:

* `classname` indicates which class implements the node's behaviour
* `input_ports` and `output_ports` specify the names and link types of ports
  * By default, ports can accept multiple connections unless the `allow_multiple_connections` is set to false.
* `metadata` provides descriptive information 

### The node constructor, and the run method

When a node is constructed, the constructor is passed a service API object, providing various useful services.  

``` py
class PrimeFactorsNode:

    def __init__(self,services):
        self.services = services
        
    def find_prime_factors(self,n):
        """Return a list of prime factors for input value n"""
        ...
        
    def run(self, inputs):
        input_values = inputs.get("data_in",[])
        if len(input_values):
            value = input_values[0]
            if not isinstance(value,int):
                raise Exception("input value {value} is not integer")
            if value < 2:
                prime_factors = [] # no solution
            else:
                prime_factors = self.find_prime_factors(value)
            return { "data_out":prime_factors }
```

As well as the `get_property` and `set_property` methods, the services API also provides methods `get_data` and `set_data` which work in a similar way - nodes may use these to read and write data represetned as a sequence of bytes.  

In general nodes may use data to persist the results of computation, for example, a machine learning model that the node has trained and then serialised to a sequence of bytes.


### Persisting node properties

Consider a node which supplies an integer values via an output port `data_out`

```
class NumberInputNode:

    def __init__(self, services):
        self.services = services

    def open_client(self,client_id, client_options, client_service):
        client_service.set_message_handler(lambda *msg: self.__handle_message(client_id, *msg))

    def __handle_message(self,client_id, value):
        if not isinstance(value,int):
            # warn that the client has provided an invalid value
            self.services.set_status_warning("New value passed by client is not integer")
        else:
            self.services.set_property("value", value)
            self.services.request_run()

    async def run(self, inputs):
        value = self.services.get_property("value", 10)
        return { "data_out": value }
```

The integer value is stored in a `value` property and the services api `get_property(name,value)` and `set_property(name,value)` are used to retrieve and update the value.

Property names must be strings and values must be JSON-serialisable objects.

The services API also provides methods to get and set binary data: `get_data(name,value)` and `set_data(name,value)` where values of type bytes.

When the node is run, its stored value is output on port `data_out`

### Clients and updating status

Clients are external routines which can communicate with nodes.  Communication happens via message passing, where each message consisting of zero or more values. 

To participate, nodes implement `open_client` and `close_client` methods.  In the example above, the `NumberInputNode` expects messages consisting of a single value, used to refresh the number stored by the node.  

Clients allow interaction with the nodes in a topology that is run interactively.

In the `NumberInputNode` example, once the node updates the value it stores it then calls the service API `request_run`, indicating that the outputs from the node have changed.  The framework will ensure that the run method will be called soon.  

If the value passed by a client is not an integer, the node will issue a warning via the service api `set_status_warning`.  The following set of service APIs related to status updates:

| service API             | Purpose                                                       |
|-------------------------|---------------------------------------------------------------|
| set_status_info(msg)    | sets the status as INFORMATIONAL accompanied by message `msg` |
| set_status_warning(msg) | sets the status as WARNING accompanied by message `msg`       |
| set_status_error(msg)   | sets the status as ERROR accompanied by message `msg`         |
| clear_status()          | clears the status associated with this node                   |

### Node lifecycle - the `reset_run`, `connections_changed` and `close` methods.

The `NumberDisplayNode` implements some code to collect input values and report thm to any connected clients.

When a topology is loaded, or when any upstream node in the topology is re-run, the node's inputs will be collected and its run method will be called.  But, before this happens, the node's `reset_run` method will be called, if it is implemented.  A node can implement this method to inform any clients that the node's current results are invalid and the node will soon be re-run.  

``` py
import json

class NumberDisplayNode:

    def __init__(self, services):
        self.services = services
        self.clients = {}

    def connections_changed(self, input_connection_counts, output_connection_counts):
        nr_integer_inputs = input_connection_counts.get("integer_data_in",0)
        nr_integerlist_inputs = input_connection_counts.get("integerlist_data_in",0)
        self.services.set_status_info(f"{nr_integer_inputs} input integers, {nr_integerlist_inputs} input integerlists")

    def reset_run(self):
        for client_id in self.clients:
            self.clients[client_id].send_message(None)

    def run(self, inputs):
        input_values = inputs.get("integer_data_in",[])+inputs.get("integerlist_data_in",[])
        txt = json.dumps(input_values)
        self.services.set_status_info(txt)
        for client_service in self.clients.values():
            client_service.send_message(txt)

    def open_client(self, client_id, client_options, client_service):
        self.clients[client_id] = client_service

    def close_client(self, client_id):
        del self.clients[client_id]

    def close(self):
        pass
```

The `reset_run` method is called as soon as the framework is aware that the node's `run` method will need to be called. 

When the topology is loaded or later updated, the number of links connected to a node's input and output ports may change.  

A node may implement a `connections_changed` method to receive notifications providing this information when a topology is first loaded and later, if these connections change:

A node may implement a `close` method to receive notifications when the node is removed from a topology

### Defining the package configuration

The package configuration is defined in a similar way to a node, with a constructor accepting a services object.

In this example, the configuration can offer a shared service to cache factorisations, that can be accessed by all nodes within the topology.

``` py
import pickle

class NumberstreamConfiguration:

    def __init__(self, services):
        self.services = services
        cache_data = services.get_data("prime_factors")
        self.prime_factor_cache = pickle.loads(cache_data) if cache_data else {}
        self.services.set_status_info(f"loaded cache ({len(self.prime_factor_cache)} items)")

    def get_prime_factors(self, n):
        if n in self.prime_factor_cache:
            return self.prime_factor_cache[n]
        else:
            return None

    def set_prime_factors(self, n, factors):
        self.prime_factor_cache[n] = factors

    def close(self):
        self.services.set_data("prime_factors", pickle.dumps(self.prime_factor_cache))
        self.services.set_status_info(f"saved cache ({len(self.prime_factor_cache)} items)")
```

The configuration is then accessed by node#s via the get_configuration service method.  Completing the definition of `PrimeFactorsNode`:

``` py
class PrimeFactorsNode:

    ...

    def is_prime(self,n):
        root = int(math.sqrt(n))
        for i in range(2, root + 1):
            if n % i == 0:
                return False
        return True

    def find_prime_factors(self,n):
        factors = self.services.get_configuration().get_prime_factors(n) or []
        if not factors:
            i = 2
            r = n
            while True:
                if r % i == 0:
                    factors.append(i)
                    r //= i
                    if self.is_prime(r):
                        break
                else:
                    i += 1
            if r > 1:
                factors.append(r)
            assert (reduce(lambda x, y: x * y, factors, 1) == n and all(self.is_prime(f) for f in factors))
            self.services.get_configuration().set_prime_factors(n, factors)
        return factors
    ...
```

For more details on the methods that a node or configuration can implement, see

* [Node abstract base class API documentation](node_api.md)
* [Configuration abstract base class API documentation](configuration_api.md)

For more details on the services API passed to node or configuration constructors, see:

* [Node services API documentation](node_service_api.md)
* [Configuration API documentation](configuration_service_api.md)


## Creating, loading and running topologies using the Hyrrokkin API

Hyrrokkin provides an API for creating, running and loading and saving topologies

``` py
from hyrrokkin.api.topology import Topology

# provide the resource path to the package containing the schema file
numberstream_package = "hyrrokkin.example_packages.numberstream"

t = Topology(execution_folder=tempfile.mkdtemp(),package_list=[numberstream_package])

t.add_node("n0", "numberstream:number_input_node", properties={"value": 99})
t.add_node("n1", "numberstream:prime_factors_node")
t.add_node("n2", "numberstream:number_display_node")

t.add_link("l0", "n0", "data_out", "n1", "data_in")
t.add_link("l1", "n1", "data_out", "n2", "integerlist_data_in")
t.run()
```

The same topology can be expressed using a YAML file

``` yaml
metadata:
  name: test topology
configuration:
  numberstream:
    readonly: false
nodes:
  n0:
    type: numberstream:number_input_node
    properties:
      value: 99
  n1:
    type: numberstream:prime_factors_node
  n2:
    type: numberstream:number_display_node
links:
- n0:data_out => n1:data_in
- n1:data_out => n2:integerlist_data_in
```

This can then be imported using the following API calls

``` py
from hyrrokkin.api.topology import Topology
from hyrrokkin.utils.yaml_importer import import_from_yaml

# provide the resource path to the package containing the schema file
numberstream_package = "hyrrokkin.example_packages.numberstream"

t = Topology(execution_folder=tempfile.mkdtemp(),package_list=[numberstream_package])
with open("topology.yaml") as f:
    import_from_yaml(t,f)
t.run()
```

Note that in the links section of the YAML file, where nodes have only one input or output port, the port name can be omitted in the links section:

```yaml
metadata:
  name: test topology
configuration:
  ...
nodes:
  ...
links:
- n0 => n1
- n1 => n2:integerlist_data_in
```

### Saving and loading topologies

A topology including its properties and data can be saved to and loaded from a serialised zip format file, using the following API calls.  Saving first:

``` py
from hyrrokkin.api.topology import Topology

# provide the resource path to the package containing the schema file
numberstream_package = "hyrrokkin.example_packages.numberstream"

t = Topology(execution_folder=tempfile.mkdtemp(),package_list=[numberstream_package])
# create or import the topology
t.run()
with open("topology.zip","wb") as f:
    t.save(f)
```

To load from a saved topology:

``` py
from hyrrokkin.api.topology import Topology

# provide the resource path to the package containing the schema file
numberstream_package = "hyrrokkin.example_packages.numberstream"

t = Topology(execution_folder=tempfile.mkdtemp(),package_list=[numberstream_package])
with open("topology.zip","rb") as f:
    t.load(f)
t.run()
```

A utility function is also provided to export a topology to YAML format.  Note that the exported YAML file contains node and configuration properties but does not contain node and configuration data.

``` py
from hyrrokkin.api.topology import Topology
from hyrrokkin.utils.yaml_exporter import export_to_yaml

# provide the resource path to the package containing the schema file
numberstream_package = "hyrrokkin.example_packages.numberstream"

t = Topology(execution_folder=tempfile.mkdtemp(),package_list=[numberstream_package])
with open("topology.zip","rb") as f:
    t.load(f)
with open("topology.yaml","w") as f:
    export_to_yaml(t,f)
```



For full details on the topology API, see:

* [Topology API documentation](topology_api.md)

## loading, saving and running topologies using topology_runner CLI

The Hyrrokkin package will install a `topology_runner` CLI command.  Some typical usages include:

Import a topology from zip and run it:

``` bash
topology_runner --package hyrrokkin.example_packages.numberstream \      
                --execution-folder /tmp/execution_test \
                --import topology.zip --run
```

Import a topology from yaml, run it and save the topology (including data) to a zip file:

``` bash
topology_runner --package hyrrokkin.example_packages.numberstream \
                --execution-folder /tmp/execution_test \
                --import topology.yaml \
                --run --export topology.zip
```

Convert a topology from zip format to yaml format, but do not run it:

``` bash
topology_runner --package hyrrokkin.example_packages.numberstream \
                --execution-folder /tmp/execution_test \
                --import topology.zip \
                --export topology.yaml
```

## Using the Hyrrokkin expression parser

Often nodes need to work with string-based expressions, for example:

`r * sin(theta)`

Hyrrokkin provides a simple expression based parser which can be set up to parse simple string based expressions into a parse tree.

```python
from hyrrokkin.utils.expr_parser import ExpressionParser
import json

ep = ExpressionParser()
ep.add_binary_operator("*",1)
print(json.dumps(ep.parse("10 * sin(pi)"),indent=2))
```

This program will print:

```json
{
   "operator": "*",
   "args": [
     {
        "literal": 10
     },
     {
       "function": "sin",
       "args": [
         {
           "name": "pi"
         }
      ]
    }
  ]
}
```

### Parser limitations

* unary and binary operators must be explicity registered with the parser 
* unary operators have higher precedence than binary operators
* binary operators must be registered with a precedence
