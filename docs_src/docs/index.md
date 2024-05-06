# Welcome to the eocis_chuk_api documentation

## Introduction

Hyrrokkin is a library which handles the execution of computational graphs, which are termed Topologies.  Each topology consists of executable components called Nodes.  Nodes communicate with each other via their ports - a Node can have input ports which are used to read in data, and output ports which are used to output data.  A topology can also contain Links, which connect the output port of one node to the input port of another.

Each link in a topology is an instance of a particular Link Type, which describes the values that can be communicated by the link.  A link type defines:

* metadata including a name and description describing what values a link of this type can convey.

Each Node in a topology is an instance of a particular Node Type, which defines:

* metadata including a name and description describing what nodes of a given type do
* the names and link types of each of its input and output ports   
* a class which implements the node's behaviour
  * most notably the class will implement a run method which transforms a set of values recieved through input ports into a set of values sent out via its output ports 

Node Types and Link Types are bundled together into a Package containing related functionality.  As well as the definition's of node and link types, a package is also described by:

* metadata including a name and description describing the purpose of the package
* a Configuration class which implements the package's behaviour
  * all node instances within a topology that belong to the package, may access a single shared instance of this Configuration class.

Each Package, and the Link Types, Node Types and Configuration it contains, is specified in a JSON formatted schema document.  

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
