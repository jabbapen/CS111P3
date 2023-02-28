## UID: 905739462
(IMPORTANT: Only replace the above numbers with your true UID, do not modify spacing and newlines, otherwise your tarfile might not be created correctly)

# Hash Hash Hash
Thread safe hash table using mutexes with a correctness version (v1) and a performant/correct version (v2)

## Building

run `make` which will generate hash-table-tester

## Running

Command: ./hash-table-tester -t [number of threads] -s [# of entries to add per thread]
Options: -t [number of threads(default 4)], -s [# of entries to add per thread(default 25000)]

Ex.
Command: ./hash-table-tester -t 4 -s 50000
Output:
Command: ./hash-table-tester -t 4 -s 50000
Output:
  Generation: 162,806 usec
  Hash table base: 634,658 usec
    - 0 missing
  Hash table v1: 2,031,322 usec
    - 0 missing
  Hash table v2: 248,238 usec
    - 0 missing
  
## First Implementation

For the first implementation strategy we simple make a static mutex lock for the hash table as a whole. When a thread wants toadd an element it takes the lock and prevents any other thread from adding to the hash table. This is essentially guaranteed to be correct because due to only 1 thread accessing the hash table as a whole its as if we are adding elements to the table in a single threaded fashion which we already know works due to it working for the starter code. This hurts performance though because we have to deal with the overhead of having multiple threads without and of the speedup.

### Performance

4 threads/cores:
Generation: 162,806 usec
Hash table base: 634,658 usec
Hash table v1: 2,031,322 usec

6 threads/cores:

As you can probably guess this is much slower than the original despite being thread safe. This is because despite using multiple threads we can't take advantage of the speed it adds

## Second Implementation

4 threads/cores:
Generation: 162,806 usec
Hash table base: 634,658 usec
For the second implementation we give each hash table entry a mutex lock rather than the hash table as a whole. The reason this works is because it's really fine if different threads add to different linked list because they won't collide with each other. The big issue comes when two threads add an element to same hash table entry at the same time causing a collision. To avoid this we give each hash table entry a lock that can be taken when an element is added to a certain entry. This prevents collision an thus allowss for thread safety

### Performance

Run the tester such that the base hash table completes in 1-2 seconds.
Report the relative speedup with number of threads equal to the number of
physical cores on your machine (at least 4). Note again that the amount of work
(`-t` times `-s`) should remain constant. Report the speedup relative to the
base hash table implementation. Explain the difference between this
implementation and your first, which respect why you get a performance increase.

## Cleaning up

run `make clean`

# CS111P3
