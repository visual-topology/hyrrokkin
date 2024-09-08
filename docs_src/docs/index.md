# Welcome to the Hyrrokkin documentation

## Introduction

### Topology

Hyrrokkin is a library which handles the execution of computational graphs, which are termed topologies.  Each topology consists of executable components called nodes.  

### Nodes, Ports and Links

Nodes are assoicated with a class which implements the node's behaviour, most notably the class will implement a `run` method which transforms a set of values recieved through that node's input ports into a set of values sent out via the node's output ports. 

``` py
class MyNode:

  def run(inputs):
    # inputs is a dictionary of K,V pairs where K is the names of an input ports 
    # and V a list of values passed to that port, collected from the values 
    # of other nodes output ports that are connected to that input port. 
    
    # process the inputs and return a dictionary of K,V pairs where K is the name of an output port and V is the value output at that port  
```

So, nodes communicate with each other via their ports - a Node defines zero or more input ports which are used to read in data, and zero our more output ports which are used to output data after the node is run.  

A topology will also contain links, which connect the output port of one node to the input port of another.


### Packages

Each node in a topology is an instance of a particular Node Type which defines the class which implements the node's functionality, and the names and Link Types of each input and output port associated with that node.  An output port of one node can only be connected to an input port of another node can only be connected by a link if they share the same Link Type.

Node Types and Link Types are bundled together into a Package containing related functionality.  As well as the definition's of node and link types, a package is also described by:

* metadata including a name and description describing the purpose of the package

* Optionally, a Configuration class which implements the package's behaviour

### Package Configuration and Schema

Each package can define a configuration class - all node instances within a topology that belong to the package, may access a single shared instance of this Configuration class.  Services and behaviours that are common to the set of nodes within a package may be conveniently delegated to this configuration class.

Each Package, and the Link Types, Node Types and optional Configuration it contains, is specified in a JSON formatted document, the schema of that Package.  

### Properties, data and the node service API

When a node or configuration is constructed, the constructor is passed a service API object, providing various useful services.  Most usefully, these services allow access to persistent storage: data and properties.

Nodes and Configurations may read and write properties.  Properties are represented by key-value pairs, where a key is a unique string and a value is any JSON-serialisable object.  Properties are usually parameters which determine the behaviour of the run method.

In the following example, we consider a node which expects numeric input values to its input port `data_in`, sums them and then adds a constant value to produce a value which is output on an output port `data_out`.


``` py
class NumberSumNode:

    def __init__(self, services):
        self.services = services

        # get the constant to be used by this node, default to 0 if not already defined
        self.constant = services.get_property("constant",0) 
        # update the property
        services.set_property("constant",self.constant)

    def run(self, inputs):
        input_values = inputs.get("data_in",[])
        output_value  = sum(input_values)+self.constant
        return { "data_out": output_value }
```

As well as the `get_property` and `set_property` methods, the services API also provides methods `get_data` and `set_data` which work in a similar way - nodes may use these to read and write data represetned as a sequence of bytes.  

In general nodes may use data to persist the results of computation, for example, a machine learning model that the node has trained and then serialised to a sequence of bytes.

### Clients

Clients are external programs which can communicate with configurations and nodes.  Communication happens via message passing, where each message consisting of zero or more values. To participate, nodes implement open_client and close_client methods.  In the following simple example, the node expects messages consisting of a single value, used to refresh the constant applied by the node.  When the node is run, we can send the new output value to any attached clients, as well as through the output port

``` py

class NumberSumNode:

  def __init__(self,services):
      self.services = services
      self.constant = services.get_property("constant",0) 
      services.set_property("constant",self.constant)
      self.clients = {}

  def open_client(self,client_id, client_options, send_fn):
      # called when a new client, assigned unique id client_id, is opened
      # send_fn is used to transmit values to the new client
      self.clients[client_id] = send_fn
      # return a function that will be called to recieve a message sent by this client
      return lambda *msg: self.__handle_message(client_id, *msg)

  def __handle_message(self,client_id,*msg):
      # called when a message is recieved from a client... update the constant
      new_constant = msg[0]
      self.constant = new_constant
      self.services.set_property("constant",self.constant)

  def close_client(self, client_id):
      # called when a client is closed
      del self.clients[client_id]

  def run(self, inputs):
        input_values = inputs.get("data_in",[])
        output_value  = sum(input_values)+self.constant
        # notify all attached clients of the new output value
        for client_id in self.clients:
            self.clients[client_id](output_value)
        return { "data_out": output_value }
```

A normal use of clients is to allow interaction with the nodes in a live topology, which may influence the properties and data associated with a node, and lead to the node being re-run.

### Node lifecycle - reset_run and request_run

When a topology is loaded, or when any upstream node in the topology is re-run, the node's inputs will be collected and its run method will be called.  But, before this happens, the node's reset_run method will be called, if it is implemented.  A node can implement this method to inform any clients that the node's current results are invalid and the node will soon be re-run.  

``` py

class NumberSumNode:

  def __init__(self,services):
      self.services = services
      self.constant = services.get_property("constant",0) 
      services.set_property("constant",self.constant)
      self.clients = {}

  def open_client(self,client_id, client_options, send_fn):
      # called when a new client, assigned unique id client_id, is opened
      # send_fn is used to transmit values to the new client
      self.clients[client_id] = send_fn
      # return a function that will be called to recieve a message sent by this client
      return lambda *msg: self.__handle_message(client_id, *msg)

  def __handle_message(self,client_id,*msg):
      new_constant = msg[0]
      if new_constant != self.constant:
          # because the constant has changed we need to re-run this node 
          self.constant = new_constant
          self.service.request_run()
      self.services.set_property("constant",self.constant)

  def close_client(self, client_id):
      del self.clients[client_id]

  def run(self, inputs):
      input_values = inputs.get("data_in",[])
      output_value  = sum(input_values)+self.constant
      for client_id in self.clients:
          self.clients[client_id](output_value)
          return { "data_out": output_value }

  def reset_run(self):
      # called when upstream changes mean that the node needs to be run
      # inform clients that any previous values sent are now invalid by 
      # sending them a None value
      for client_id in self.clients:
          self.clients[client_id](None)
```

The `reset_run` method is usually called as soon as it is known that the node's `run` method will need to be called. 

Another way in which the node is re-run is when a node itself invokes the service API  `request_run` method, often in response to the interaction between a node and its clients.  In this example, this happens when a client sends a new constant value for the node to use.

### Reporting status

A number of service API methods allow the node to report its status, classified as either info, warning or error, and also to clear any previously reported status.

``` py

class NumberSumNode:

  def __init__(self,services):
      self.services = services
      self.constant = services.get_property("constant",0) 
      services.set_property("constant",self.constant)
      self.clients = {}

  def open_client(self,client_id, client_options, send_fn):
      self.clients[client_id] = send_fn
      return lambda *msg: self.__handle_message(client_id, *msg)

  def __handle_message(self,client_id,*msg):
      new_constant = msg[0]
      if not (isinstance(new_constant,int) or isinstance(new_constant,float)):
          # warn that the client has provided an invalid value
          self.services.set_status_warning("New constant requested by client is neither integer nor float, ignoring") 
      if new_constant != self.constant:
          self.constant = new_constant
          self.services.set_property("constant",self.constant)
          self.service.request_run()
          # inform that the constant has been updated
          self.services.set_status_info("Constant updated, awaiting re-run")

  def close_client(self, client_id):
      del self.clients[client_id]

  def run(self, inputs):
      try:
          input_values = inputs.get("data_in",[])
          output_value  = sum(input_values)+self.constant
          for client_id in self.clients:
              self.clients[client_id](output_value)
              return { "data_out": output_value }
          # clear the status after a successful execution    
          self.services.clear_status()
      except Exception as ex:
          # something has gone wrong, set the status to error
          self.services.set_status_error(f"Run failed due to {str(ex)}") 
          # raising an exception within the run method indicates that the node has 
          # failed 
          raise

  def reset_run(self):
      for client_id in self.clients:
          self.clients[client_id](None)
```

### Understanding connections

When the topology is updated, the number of links connected to a node's input and output ports may be updated.  A node may implement a `connections_changed` method to recieve notifications providing this information when a topology is first loaded and later, if these connections change:

``` py

class NumberSumNode:

    ...

    def connections_changed(self, input_connection_counts, output_connection_counts):
        if self.input_connection_counts["data_in"] == 0:
            self.services.set_status_warning("No inputs are currently connected")
```

### Obtaining the configuration instance

If the node belongs to a package which defines a configuration class, the node can obtain an instance of that class which is shared amonst all nodes belonging to that package.  In the example below, a configuration class controls whether nodes are able to be modified by clients or if they are read-only.


``` py

class NumberSumNode:

    ...
    def __init__(self,services):
        self.services = services
        self.constant = services.get_property("constant",0) 
        services.set_property("constant",self.constant)
        self.clients = {}
        # if no configruation class is defined for this node's package, 
        # get_configuration() will return None
        self.configuration = services.get_configuration()
        self.is_readonly = self.configuration.get_is_readonly()
    
    def open_client(self,client_id, client_options, send_fn):
        self.clients[client_id] = send_fn
        if self.is_readonly:
            return None # ignore messages from this client 
        else:
            return lambda *msg: self.__handle_message(client_id, *msg)

    ...

```

The configuration class is implemented in a similar way to a node

``` py
class NumberstreamConfiguration:

    def __init__(self, services):
        # the services API is similar to that provided to a node
        # except that the reset_run method is not supported
        self.services = services 

    def get_is_readonly(self):
        return self.services.get_property("readonly",False)
```

The methods `run`, `reset_run` and `connections_changed` methods are also not used for configuration classes - configurations have no connections and cannot be run.  They can, however, communicate with clients in the same way that nodes can, and so the same methods `open_client` and `close_client` described above for nodes can also be implemented for configurations. 

Similarly, the service API for configurations is the same as that for nodes, except that the `request_run` method is not present.  Configurations can read and write data and properties, and issue status updates in the same way that nodes can.

For more details on the methods that a node or configuration can implement, see

* [Node abstract base class API documentation](node_api.md)
* [Configuration abstract base class API documentation](configuration_api.md)

For more details on the services API passed to node or configuration constructors, see:

* [Node services API documentation](node_service_api.md)
* [Configuration API documentation](configuration_service_api.md)

## Defining a Package schema using JSON

A package is defined by a schema, written in JSON

Each schema starts with some metadata, in particular a unique idenfifier for the package:

``` json
{
    "id": "numberstream",
    "metadata": {
        "name": "Number Stream",
        "version": "0.0.1",
        "description": "package for generating and manipulating streams of numbers"
    },
    ...
}
```

Next we define the configuration:

``` json
{
    ...
    "dependencies": [],
    "configuration": {
        "classname": "numberstream_configuration.NumberstreamConfiguration"
    },
    ...
}
```

Now we introduce the node types, specifying some metadata, the classname, and the definition of any import and output ports:

``` json
{   
    ...
    "node_types": {
        "number_input_node": {
            "metadata": {
                "name": "Input Number Node",
                "description": "Input a number"
            },
            "output_ports": {
                "data_out": {
                    "link_type": "numberstream:number"
                }
            },
            "classname": "nodes.number_input_node.NumberInputNode"
        },
        "sum_node": {
            "metadata": {
                "name": "Number Sum",
                "description": "Sum any input number(s) received"
            },
            "input_ports": {
                "data_in": {
                    "link_type": "numberstream:number"
                }
            },
            "output_ports": {
                "data_out": {
                    "link_type": "numberstream:number"
                }
            },
            "classname": "nodes.sum_node.SumNode"
        },
         "number_display": {
            "metadata": {
                "name": "Number Display",
                "description": "Display any received number(s)"
            },
            "input_ports": {
                "data_in": {
                    "link_type": "numberstream:number",
                    "allow_multiple_connections": false
                }
            },
            "output_ports": {
            },
            "classname": "nodes.number_display_node.NumberDisplayNode"
        }
    },
    ...
}
```

When defining an input or output port for a node type, the number of connections that can be made to that port can be limited to 1 by specifying `allow_multiple_connections:false`.

Finally the definitions of any link types associated with any input and output ports are declared.  In this simple example, only one link type is used:

``` json
{
    ...
    "link_types": {
        "number": {
            "metadata": {
                "name": "Number",
                "description": "Carry a single number"
            }
        }
    }
}
```

When refering to a link type, the package id should be used as a prefix, `<package-id>:<link-type-id>`.  In this example, `numberstream:number` refers to the link type `number` defined in the `numberstream` example package.  This allows packages to refer to link types defined in other packages when defining nodes.

## Creating, loading and running topologies using the Hyrrokkin API

Hyrrokkin provides an API for creating, running and loading and saving topologies

``` py
from hyrrokkin.api.topology import Topology

# provide the resource path to the package containing the schema file
numberstream_package = "hyrrokkin_example_packages.numberstream"

t = Topology(execution_folder=tempfile.mkdtemp(),package_list=[numberstream_package])
t.set_metadata({"name":"test_topology")
t.set_configuration_property("numberstream","readonly",False)
t.add_node("n0", "numberstream:number_input_node", {"value":99})
t.add_node("n1", "numberstream:sum_node", {"constant":42})
t.add_node("n2", "numberstream:number_display_node", {})

t.add_link("l0", "n0", "data_out", "n1", "data_in")
t.add_link("l1", "n1", "data_out", "n2", "data_in")
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
    type: numberstream:number_sum_node
    properties:
      constant: 42
  n2:
    type: numberstream:number_display_node
    properties: {}
links:
- n0:data_out => n1:data_in
- n1:data_out => n2:data_in
```

This can then be imported using the following API calls

``` py
from hyrrokkin.api.topology import Topology
from hyrrokkin.utils.yaml_importer import import_from_yaml

# provide the resource path to the package containing the schema file
numberstream_package = "hyrrokkin_example_packages.numberstream"

t = Topology(execution_folder=tempfile.mkdtemp(),package_list=[numberstream_package])
with open("topology.yaml") as f:
    import_from_yaml(t,f)
t.run()
```

Note that in the links section of the YAML file, where nodes have only one input or output port, the port name can be omitted:

```yaml
metadata:
  name: test topology
configuration:
  ...
nodes:
  ...
links:
- n0 => n1
- n1 => n2
```

### Saving and loading topologies

A topology including its properties and data can be saved to and loaded from a serialised zip format file, using the following API calls.  Saving first:

``` py
from hyrrokkin.api.topology import Topology

# provide the resource path to the package containing the schema file
numberstream_package = "hyrrokkin_example_packages.numberstream"

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
numberstream_package = "hyrrokkin_example_packages.numberstream"

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
numberstream_package = "hyrrokkin_example_packages.numberstream"

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
topology_runner --package hyrrokkin_example_packages.numberstream \      
                --execution-folder /tmp/execution_test \
                --import topology.zip --run
```

Import a topology from yaml, run it and save the topology (including data) to a zip file:

``` bash
topology_runner --package hyrrokkin_example_packages.numberstream \
                --execution-folder /tmp/execution_test \
                --import topology.yaml \
                --run --export topology.zip
```

Convert a topology from zip format to yaml format, but do not run it:

``` bash
topology_runner --package hyrrokkin_example_packages.numberstream \
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

ep = ExpressionParser()
ep.add_binary_operator("*",1)
print(JSON.dumps(ep.parse("10 * sin(pi)",intent=2)))
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
