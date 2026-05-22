"""
Engine-level runtime state primitives.

Public API::

    from pygame_engine.state import flags             # RuntimeFlags singleton
    from pygame_engine.state import RuntimeFlags      # class for subclassing
    from pygame_engine.state import Observable        # reactive value wrapper
    from pygame_engine.state import SubscriptionGroup # subscription lifecycle
"""

from pygame_engine.state.observable import Observable
from pygame_engine.state.runtime_flags import RuntimeFlags, flags
from pygame_engine.state.subscription_group import SubscriptionGroup

__all__ = ["Observable", "RuntimeFlags", "SubscriptionGroup", "flags"]
