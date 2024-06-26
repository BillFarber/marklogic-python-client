---
layout: default
title: Executing code
nav_order: 7
---

The [MarkLogic REST service extension](https://docs.marklogic.com/REST/client/service-extension) supports the
execution of custom code, whether via an inline script or an existing module in your application's modules database. 
The MarkLogic Python client supports execution of custom code by simplifying the submission of custom code
and converting the multipart response into more useful Python data types.

## Table of contents
{: .no_toc .text-delta }

- TOC
{:toc}

## Setup

The examples below all depend on the instructions in the [setup guide](example-setup.md) having already been performed.

To try out the examples, start a Python shell and first run the following:

```
from marklogic import Client
client = Client('http://localhost:8000', digest=('python-user', 'pyth0n'))
```

## Executing ad-hoc queries

The [v1/eval REST endpoint](https://docs.marklogic.com/REST/POST/v1/eval) supports the execution of ad-hoc JavaScript 
and XQuery queries. Each type of query can be easily submitted via the client:

```
client.eval(javascript="fn.currentDateTime()")
client.eval(xquery="fn:current-dateTime()")
```

Variables can optionally be provided via a `dict`:

```
results = client.eval(javascript='Sequence.from([{"hello": myValue}])', vars={"myValue": "world"})
assert "world" == results[0]["hello"]
```

Because the REST endpoint returns a sequence of items, the client will always return a list of values. See the section
below on how data types are converted to understand how the client will convert each value into an appropriate Python
data type.

## Invoking modules

The [v1/invoke REST endpoint](https://docs.marklogic.com/REST/POST/v1/invoke) supports the execution of JavaScript
and XQuery main modules that have been deployed to your application's modules database. 

If you wish to attempt the examples below (instead of invoking your own modules), first run the following to 
insert a simple runnable module into the out-of-the-box "Modules" database:

```
from marklogic.documents import Document
module = Document('/sample.sjs', 'const doc = {"hello": "world"}; doc', permissions={"rest-reader": ["read", "update", "execute"]})
client.documents.write(module, params={"database": "Modules"})
```

A module can be invoked via the client in the following manner:

```
# Set the input to the URI of the module you wish to invoke in your application's 
# modules database.
client.invoke("/sample.sjs")
```

You can provide variables to your module in the same fashion as when evaluating custom 
code (the variable will not have any impact on the sample module loaded above; this is
shown purely to demonstrate how to define variables):

```
client.invoke("/sample.sjs", vars={"my_var1": "value1"})
```

## Conversion of data types

The REST endpoints for evaluating ad-hoc code and for invoking a module both return a sequence of values, with each 
value having MarkLogic-specific type information. The client will use this type information to convert each value into
an appropriate Python data type. For example, each JSON object into the example below is converted into a `dict`:

```
results = client.eval(javascript='Sequence.from([{"doc": 1}, {"doc": 2}])')
assert len(results) == 2
assert results[0]["doc"] == 1
assert results[1]["doc"] == 2
```

The following table describes how each MarkLogic type is associated with a Python data type. For any 
MarkLogic type not listed in the table, such as `hexBinary` and `base64Binary`, the value is not converted and will 
remain of type `bytes`. 

| MarkLogic type | Python type | 
| --- | --- |
| string | str |
| integer | int |
| boolean | bool |
| decimal | [Decimal](https://docs.python.org/3/library/decimal.html) |
| map | dict |
| element() | str |
| array | list |
| array-node() | list |
| object-node() | dict or `marklogic.documents.Document` |
| document-node() | str or `marklogic.documents.Document` |
| binary() | bytes or `marklogic.documents.Document` | 

For the `object-node()`, `document-node()`, and `binary()` entries in the above table, a 
`marklogic.documents.Document` instance will be returned if the value is associated with a URI via 
the multipart `X-URI` header. Otherwise, a value of type `dict`, `str`, or `bytes` is returned respectively.

## Returning the original HTTP response

Each `client.eval` method and `client.invoke` accept a `return_response` argument. When that
argument is set to `True`, the original response is returned. This can be useful for custom
processing of the response or debugging requests.

## Referencing a transaction

The `client.eval` and `client.invoke` functions both support referencing a 
[REST API transaction](https://docs.marklogic.com/REST/client/transaction-management) via the `tx` 
argument. See [the guide on transactions](transactions.md) for further information.

## Providing additional arguments

The `client.eval` and `client.invoke` methods each provide a `**kwargs` argument, so you can pass in any other arguments you would
normally pass to `requests`. For example:

```
client.eval(javascript="fn.currentDateTime()", params={"database": "Documents"})
client.invoke("/sample.sjs", params={"database": "Documents"})
```

Please see [the eval endpoint documentation](https://docs.marklogic.com/REST/POST/v1/eval) 
and [the invoke endpoint documentation](https://docs.marklogic.com/REST/POST/v1/invoke) for
information on additional parameters.
