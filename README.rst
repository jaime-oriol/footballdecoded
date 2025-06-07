FootballDecoded
===============

Professional football data extraction and analysis toolkit.

Features
--------

* FBref complete data extraction
* Understat advanced metrics
* WhoScored spatial coordinates
* Professional tactical analysis

Installation
------------

.. code-block:: bash

    pip install -e .

Usage
-----

.. code-block:: python

    from scrappers import FBref
    from wrappers import fbref_get_player
    
    # Extract player data
    player_data = fbref_get_player("Mbappé", "ESP-La Liga", "2024-25")

License
-------

MIT License
