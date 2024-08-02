import multiprocessing
from multiprocessing import Process, SimpleQueue
import time
import os

def test_func(queue):
    print("Process function is running")
    time.sleep(2)
    queue.put("Process function completed")

if __name__ == "__main__":
    multiprocessing.set_start_method('fork')
    
    print("Before Process")
    q = SimpleQueue()
    try:
        p = Process(target=test_func, args=(q,))
        p.start()
        p.join()  # Wait for the process to complete
        while not q.empty():
            print(q.get())
        print("Process started and completed successfully")
    except Exception as e:
        print(f"Failed to start process: {e}")

