# -*- coding: utf-8 -*-

import os
import sys

from functools import wraps

def measure_time(f):
  @wraps(f)
  def wrapper(*args,**kwargs):
      t = time.time()
      res = f(*args,**kwargs)
      print("Function took " + str(time.time()-t) + " seconds to run")
      return res
  return wrapper

def block_print(f):
    @wraps(f)
    def wrapper(*args,**kwargs):

        # store original
        original_stdout = sys.stdout

        # block all printing to the console
        sys.stdout = open(os.devnull, 'w')

        # call function f
        res = f(*args, **kwargs)

        # recover original stdout
        sys.stdout.close()
        sys.stdout = original_stdout

        # return function value
        return res
    return wrapper