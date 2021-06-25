# memoizer_with_timeout
 Memoization decorator with timeout on function results.
 
 Intended to be used on long-running APIs that do not require frequent updates
 
Usage example
```
@TimedMemoizer(30)
def foo(*args):
    return args
```
will create a decorated function where TTL of each cached result will be 30 seconds.

Stale cached results for __all decorated APIs__ are cleaned on periodic audits, that may be invoked on a call to any decorated function. Autit frequency is defined by the *\__CACHE_AUDIT_TO* attribute of the decorator class.

User-initiated cache clean-up - per decorated function - can be done by calling *clear* attribute of the decorated function
```
foo.clear()
```
