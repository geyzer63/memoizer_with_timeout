from functools import partial, wraps
from time import time
from threading import Lock

class TimedMemoizer:
    """ 
    Memoization decorator, caching function call results with a timeout.
    For each call, result cache expires when a call time for a function with 
    cached argument set /return value is greater than cached expiration 
    timestamp for that argument set.
    On a call to any decorated function, cache audit may be invoked
    in order to clear stale cached results and prevent potential memory leak.
    """
    __CACHE_AUDIT_TO = 1800
    __instances = []
    __closest_audit_ts = time() + __CACHE_AUDIT_TO
    
    @classmethod
    def __run_stale_caches_audit(cls, now):
        """ Executes clean-up of stale cached calls over all instances """
        if cls.__closest_audit_ts < now:
            cls.__closest_audit_ts = time() + cls.__CACHE_AUDIT_TO
            with Lock():
                for instance in cls.__instances:
                    instance.__clear_stale_results(now)
    
    def __init__(self, timeout):
        self.__cache = {}
        self.__timeout = timeout
        self.__next_audit_ts = 0
        self.__class__.__instances.append(self)
        self.__set_next_audit(time())
    
    def __set_next_audit(self, now):
        self.__next_audit_ts = max(now + self.__timeout,
                                   self.__class__.__closest_audit_ts)
    
    def __clear(self):
        """ Allows clearing of all cached results """
        self.__cache.clear()
    
    def __clear_stale_results(self, now):
        """ CLean-up stale function cache """
        if self.__next_audit_ts < now:
            self.__cache = {
                result_key: (result, expires_at)
                for result_key, (result, expires_at) in self.__cache.items()
                if expires_at > now
            }
            self.__set_next_audit(now)
        
    def __call__(self, func):
        setattr(func, 'clear', self.__clear)
        @wraps(func)
        def caller(*args, **kwargs):
            now = int(time())
            self.__class__.__run_stale_caches_audit(now)

            result_key = hash(f'{args}{kwargs}')
            result, expires_at = self.__cache.get(result_key, (None, 0))
            if expires_at > now:
                return result
            
            expires_at = now + self.__timeout
            result = func(*args, **kwargs)
            self.__cache[result_key] = result, expires_at
            return result
            
        return caller
