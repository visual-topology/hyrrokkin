# Welcome to Hyrrokkin's documentation

## Introduction

Hyrrokkin is a python library which manages the execution of computational graphs, termed topologies.  Each topology consists of one or more executable components called nodes.  
Nodes communicate with each other via their ports - a node can have input ports which are used to read in data, and output ports which are used to output data.  

A topology can also contain links, which connect the output port of one node to the input port of another.

Each node is an instance of a node type which defines:

* the names of each of its input and output ports and the types of links that can be connected to them  
* a class which implements the node's behaviour
  * most importantly the class will implement a run method which transforms a set of values received through input ports into a set of values sent out via its output ports 

Sets of node types which implement related functionality are bundled together into a package and described in the package schema, a JSON formatted file.  

As well as the definition's of node types, a package is also described by:

* metadata including a name and description describing the purpose of the package
* a configuration class which implements package-level behaviour
  * all node instances within a topology that belong to the package, may access a single shared instance of this Configuration class.

Each package and the node, link and configuration types it contains, is specified in a JSON formatted schema document.  

## Properties and data

Nodes and Configurations may read and write properties.  Properties are represented by key-value pairs, where a key is a string and a value is any JSON-serialisable object.  Properties can be thought of as parameters which determine the execution of the node.

Nodes and Configurations may also read and write data.  Data are represented by key-value pairs, where a key is a string and a value is a sequence of bytes.  Data are usually used to hold some intermediate or re-usable results of a computation. 

## Node API

In hyrrokkin, nodes are implemented using a python class which implements methods described in `hyrrokkin.base.node_base.NodeBase`:

::: hyrrokkin.base.node_base

## Node Services API

::: hyrrokkin.services.node_services

## Creating, loading and running topologies

::: hyrrokkin.api.topology
