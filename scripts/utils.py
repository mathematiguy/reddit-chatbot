import time
import hashlib
from multiprocessing import Pool, cpu_count

def md5_string(s):
    hash_md5 = hashlib.md5()
    hash_md5.update(s)
    return hash_md5.hexdigest()


def sha256(filepath):
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def multicore_apply(iterable, func):
    '''
    Implements pool.map safely, closing processes properly afterwards
    '''
    try:
        pool = Pool(cpu_count() - 1)
        result = pool.map(func, iterable)
    finally:
        pool.close()
        pool.join()
    return result


def timeit(method):

    def print_timing(te, ts, args, kw):
        mins, secs = divmod(te - ts, 60)
        hours, mins = divmod(mins, 60)
        print("Timeit results for '{}'".format(method.__name__))
        print('Args:', args)
        print('Kwargs:', kw)
        print('Time to execute: {:02d}:{:02d}:{:02d}'.format(int(hours), int(mins), int(secs)))

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print_timing(te, ts, args, kw)
        return result

    return timed


if __name__ == "__main__":
    pass