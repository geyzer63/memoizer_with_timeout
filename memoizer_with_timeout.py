from functools import partial, wraps
from time import time
from threading import Lock

class TimedMemoizer:
    """ 
    Memoization decorator, caching function call results till 
    call time for the combination of function and argument values is 
    greater than cached expiration timestamp.
    On a call to any decorated function, cache audit may be invoked
    in order to clear stale cached results and prevent potential memory leak.
    """
    __CACHE_AUDIT_TO = 1800
    __cache = {}
    __next_cleanup = time()
    
    @classmethod
    def __stale_cache_clear(cls, now):
        """ Executes clean-up of stale cached calls """
        stale_results = []
        for func, func_cache in cls.__cache.items():
            for result_key, (_, expires_at) in func_cache.items():
                if expires_at < now:
                    stale_results.append((func, result_key))
                        
        for func, result_key in stale_results:
            cls.__cache[func].pop(result_key)
            if not cls.__cache[func]:
                cls.__cache.pop(func)
        cls.__next_cleanup = now + cls.__CACHE_AUDIT_TO
   
    def __init__(self, timeout):
        self.timeout = timeout
    
    @classmethod
    def __clear(cls, func):
        """ Allows clearing of all cached results for a specific function """
        cls.__cache.pop(func)
        
    def __call__(self, func):
        clazz = self.__class__
        setattr(func, 'clear', partial(clazz.__clear, func))
        @wraps(func)
        def caller(*args, **kwargs):
            now = int(time())
            if now > clazz.__next_cleanup:
                # Execute next cache audit
                with Lock():
                    clazz.__stale_cache_clear(now)

            func_cache = clazz.__cache.setdefault(func, {})
            result_key = hash(f'{args}{kwargs}')
            result, expires_at = func_cache.get(result_key, (None, 0))
            if expires_at > now:
                return result
            
            expires_at = now + self.timeout
            result = func(*args, **kwargs)
            func_cache[result_key] = result, expires_at

            
            return result
            
        return caller
