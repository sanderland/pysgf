PySGF Documentation
===================


.. contents::
   :local:

Installation
^^^^^^^^^^^^
To install this package:

.. code-block:: bash

   pip install pysgf

Documentation
^^^^^^^^^^^^^

GoGame
------
.. autoclass:: pysgf.GoGame
    :members:
    :undoc-members:
    :member-order: bysource

GoNode
------
.. autoclass:: pysgf.GoNode
    :members:
    :undoc-members:
    :member-order: bysource

Subclassing
-----------
``GoGame`` and ``GoNode`` are the ready-to-use concrete classes. To attach your own
data or behaviour to nodes, subclass the generic bases instead, so that ``parent``,
``children`` and ``play()`` all stay typed as your own node class:

.. code-block:: python

   from pysgf import BaseGoGame, BaseGoNode

   class MyNode(BaseGoNode["MyNode"]):
       ...

   class MyGame(BaseGoGame[MyNode]):
       NODE_TYPE = MyNode

.. autoclass:: pysgf.BaseGoNode
    :members:
    :undoc-members:
    :member-order: bysource

.. autoclass:: pysgf.BaseGoGame
    :members:
    :undoc-members:
    :member-order: bysource


Move
----
.. autoclass:: pysgf.Move
    :members:
    :member-order: bysource

ParseError
----------
.. autoclass:: pysgf.ParseError
