import threading
import time

def log(msg):
    print msg

class ThreadPool:   
    def __init__(self, numThreads):
        self._threads = []
        self._resizeLock = threading.Condition(threading.Lock())
        self._taskLock  = threading.Condition(threading.Lock())
        self._tasks = []
        self._isJoining = False
        self.setThreadCount(numThreads)
    
    def setThreadCount(self, newNumThreads):
        if self._isJoining:
            return False
        
        self._resizeLock.acquire()
        try:
            self.__setThreadCountNolock(newNumThreads)
        finally:
            self._resizeLock.release()
        
        return True
    
    def __setThreadCountNolock(self, newNumThreads):
        while newNumThreads > len(self._threads):
            newThread = ThreadPoolThread(self)
            self._threads.append(newThread)
            newThread.start()
            
        while newNumThreads < len(self._threads):
            self._threads[0].goAway()
            del self._threads[0]
            
    def getThreadCount(self):
        self._resizeLock.acquire()
        try:
            return len(self._threads)
        finally:
            self._resizeLock.release()
            
    def queueTask(self, task, args=None, taskCallback=None):
        if self._isJoining == True:
            return False
        if not callable(task):
            return False
        
        self._taskLock .acquire()
        try:
            self._tasks.append((task, args, taskCallback))
            return True
        finally:
            self._taskLock .release()
            
    def getNextTask(self):
        self._taskLock .acquire()
        try:
            if self._tasks == []:
                return (None, None, None)
            else:
                return self._tasks.pop(0)
        finally:
            self._taskLock .release()
    
    def joinAll(self, waitForTasks=True, waitForThreads=True):
        self._isJoining = True
        
        if waitForTasks:
            while self._tasks != []:
                time.sleep(0.1)
        
        self._resizeLock.acquire()
        try:
            self.__setThreadCountNolock(0)
            self._isJoining = True
            
            if waitForThreads:
                for t in self._threads:
                    t.join()
                    del t
            
            self._isJoining = False
        finally:
            self._resizeLock.release()
            
class ThreadPoolThread(threading.Thread):
    threadSleepTime = 0.1
    
    def __init__(self, pool):
        threading.Thread.__init__(self)
        self._pool = pool
        self._kill = False
        
    def run(self):
        while self._kill == False:
            cmd, args, callback = self._pool.getNextTask()
            if cmd is None:
                time.sleep(ThreadPoolThread.threadSleepTime)
            elif callback is None:
                cmd(args)
            else:
                callback(cmd(args))
                
    def goAway(self):
        self._kill = True
        
def main():
    def wait(data):
        log("Sleeping for %ss" % data)
        time.sleep(data)
        
        return {'cmd':'wait', 'data':data}
        
    def waitCallback(data):
        log("Callback:", data)
        
    pool = ThreadPool(3)
    for x in range(0,10):
        pool.queueTask(wait, 5, waitCallback)
    
    pool.joinAll()

if __name__ == '__main__':
    main()
