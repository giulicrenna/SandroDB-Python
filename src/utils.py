from types import ModuleType, FunctionType
from gc import get_referents
import threading
import functools
import sys
import time
from queue import Queue

BLACKLIST = type, ModuleType, FunctionType

"""
The getsize() function calculates the total size of an object and all of its members.
It does this by recursively traversing the object and its members, 
and adding the size of each object to the total.
"""
def getsize(obj):
    """sum size of object & members."""
    if isinstance(obj, BLACKLIST):
        raise TypeError('getsize() does not take argument of type: '+ str(type(obj)))
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += sys.getsizeof(obj)
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size

"""
The threaded decorator is a function that takes another function as an argument and returns a new function. 
The new function wraps the original function and launches it in a separate thread. 
This allows the original function to run concurrently with other code,
which can improve performance in some cases.

The @functools.wraps(func) decorator is used to preserve the name,
docstring, and other attributes of the original function in the new function.
This makes it easier to debug and maintain the code.

The thread = threading.Thread(target=func, args=args, kwargs=kwargs)
line creates a new thread that will run the original function.
The target parameter specifies the function to be run,
and the args and kwargs parameters specify the arguments to be passed to the function.

The thread.start() line starts the thread,
which causes the original function to run concurrently with other code.

The return thread line returns the thread object to the caller.
This allows the caller to wait for the thread to finish or to check its status.
"""
def threaded(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Create a queue to store the result
        result_queue = Queue()

        # Define the target function that executes the decorated function
        def target():
            result_queue.put(func(*args, **kwargs))
        
        # Create and start the thread
        thread = threading.Thread(target=target)
        thread.start()
        
        time.sleep(3)


        # Return the thread object and the queue
        return thread, result_queue

    return wrapper