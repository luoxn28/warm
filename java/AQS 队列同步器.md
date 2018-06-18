
**队列同步器AbstractQueuedSynchronizer（以下简称同步器），是用来构建锁或者其他同步组件的基础框架，它使用了一个int成员变量表示同步状态，通过内置的FIFO队列来完成资源获取线程的排队工作**，并发包的作者（Doug Lea）期望它能够成为实现大部分同步需求的基础。

同步器的主要使用方式是继承，子类通过继承同步器并实现它的抽象方法来管理同步状态，在抽象方法的实现过程中免不了要对同步状态进行更改，这时就需要使用同步器提供的3个方法（getState()、setState(int newState)和compareAndSetState(int expect,int update)）来进行操作，因为它们能够保证状态的改变是安全的。子类推荐被定义为自定义同步组件的静态内部类，同步器自身没有实现任何同步接口，它仅仅是定义了若干同步状态获取和释放的方法来供自定义同步组件使用，同步器既可以支持独占式地获取同步状态，也可以支持共享式地获取同步状态，这样就可以方便实现不同类型的同步组件（ReentrantLock、ReentrantReadWriteLock和CountDownLatch等）。

同步器是实现锁（也可以是任意同步组件）的关键，在锁的实现中聚合同步器，利用同步器实现锁的语义。可以这样理解二者之间的关系：锁是面向使用者的，它定义了使用者与锁交互的接口（比如可以允许两个线程并行访问），隐藏了实现细节；同步器面向的是锁的实现者，它简化了锁的实现方式，屏蔽了同步状态管理、线程的排队、等待与唤醒等底层操作。锁和同步器很好地隔离了使用者和实现者所需关注的领域。

### AQS接口

同步器的设计是基于模板方法模式的，也就是说，使用者需要继承同步器并重写指定的方法，随后将同步器组合在自定义同步组件的实现中，并调用同步器提供的模板方法，而这些模板方法将会调用使用者重写的方法。

同步器的设计是基于模板方法模式的，也就是说，使用者需要继承同步器并重写指定的方法，随后将同步器组合在自定义同步组件的实现中，并调用同步器提供的模板方法，而这些模板方法将会调用使用者重写的方法。

重写同步器指定的方法时，需要使用同步器提供的如下3个方法来访问或修改同步状态。
- getState()：获取当前同步状态。
- setState(int newState)：设置当前同步状态。
- compareAndSetState(int expect,int update)：使用CAS设置当前状态，该方法能够保证状态设置的原子性。

同步器可重写的方法与描述如下：

<img src="./_image/AQS 队列同步器/21-55-22.jpg"/>

实现自定义同步组件时，将会调用同步器提供的模板方法，这些（部分）模板方法与描述如下：

<img src="./_image/AQS 队列同步器/21-55-47.jpg"/>

同步器提供的模板方法基本上分为3类：**独占式获取与释放同步状态、共享式获取与释放同步状态和查询同步队列中的等待线程情况**。自定义同步组件将使用同步器提供的模板方法来实现自己的同步语义。独占式锁示例可以查看Java `ReentrantLock`源码。

### AQS实现分析

AQS是如何完成线程同步的，主要包括：**同步队列、独占式同步状态获取与释放、共享式同步状态获取与释放以及超时获取同步状态等同步器的核心数据结构与模板方法**。

#### 同步队列

同步器依赖内部的同步队列（一个FIFO双向队列）来完成同步状态的管理，当前线程获取同步状态失败时，同步器会将当前线程以及等待状态等信息构造成为一个节点（Node）并将其加入同步队列，同时会阻塞当前线程，当同步状态释放时，会把首节点中的线程唤醒，使其再次尝试获取同步状态。

同步队列中的节点（Node）用来保存获取同步状态失败的线程引用、等待状态以及前驱和后继节点，节点的属性类型与名称。

<img src="./_image/AQS 队列同步器/22-18-11.jpg"/>

节点是构成同步队列的基础，同步器拥有首节点（head）和尾节点（tail），没有成功获取同步状态的线程将会成为节点加入该队列的尾部。因为同步队列会涉及到多线程操作，所以入队列必须是线程安全的，因此同步器提供了一个基于CAS的设置尾节点的方法：compareAndSetTail(Node expect,Nodeupdate)，它需要传递当前线程“认为”的尾节点和当前节点，只有设置成功后，当前节点才正式与之前的尾节点建立关联。

<img src="./_image/AQS 队列同步器/22-17-52.jpg"/>

同步队列遵循FIFO，首节点是获取同步状态成功的节点，首节点的线程在释放同步状态时，将会唤醒后继节点，而后继节点将会在获取同步状态成功时将自己设置为首节点。设置首节点是通过获取同步状态成功的线程来完成的，由于只有一个线程能够成功获取到同步状态，因此设置头节点的方法并不需要使用CAS来保证，它只需要将首节点设置成为原首节点的后继节点并断开原首节点的next引用即可。

<img src="./_image/AQS 队列同步器/22-21-14.jpg"/>

设置首节点是通过获取同步状态成功的节点来完成的，由于只有一个线程能够获取到同步状态，因此设置头结点不需要使用CAS来保证，它只需要将首节点设置成原首节点的后继节点并断开原首节点的next引用即可。

#### 独占式同步状态获取与释放

以ReentrantLock的lock/unlock为例说明独占式同步状态获取与释放，代码示例如下：
```Java
Lock lock = new ReentrantLock();
lock.lock();
 
Thread thread = new Thread(() -> {
    lock.lock();
    lock.unlock();
}, "thread1");
thread.start();
 
Thread.sleep(1000);
lock.unlock();
 
thread.join();
```

调用`lock.lock()`，会执行到`NonfairSync.lock()`，这里会首先进行CAS状态，成功即表示lock成功，否则调用`acquire(1)`获取同步状态。
```Java
final void lock() {
	if (compareAndSetState(0, 1))
		setExclusiveOwnerThread(Thread.currentThread());
	else
		acquire(1);
}
```

通过调用同步器的acquire(int arg)方法可以获取同步状态，该方法对中断不敏感，也就是由于线程获取同步状态失败后进入同步队列中，后续对线程进行中断操作时，线程不会从同步队列中移出。
```Java
public final void acquire(int arg) {
    if (!tryAcquire(arg) && // tryAcquire(arg)再次尝试CAS
        acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
        selfInterrupt();
}
     
private Node addWaiter(Node mode) {
    Node node = new Node(Thread.currentThread(), mode);
    // Try the fast path of enq; backup to full enq on failure
    Node pred = tail;
    if (pred != null) {
        node.prev = pred;
        if (compareAndSetTail(pred, node)) {
            pred.next = node;
            return node;
        }
    }
    enq(node);
    return node;
}
private Node enq(final Node node) {
    for (;;) {
        Node t = tail;
        if (t == null) { // Must initialize
            if (compareAndSetHead(new Node()))
                tail = head;
        } else {
            node.prev = t;
            if (compareAndSetTail(t, node)) {
                t.next = node;
                return t;
            }
        }
    }
}
```

在enq(final Node node)方法中，同步器通过“死循环”来保证节点的正确添加，在“死循环”中只有通过CAS将节点设置成为尾节点之后，当前线程才能从该方法返回，否则，当前线程不断地尝试设置。可以看出，enq(final Node node)方法将并发添加节点的请求通过CAS变得“串行化”了。

节点进入同步队列之后，就进入了一个自旋的过程，每个节点（或者说每个线程）都在自省地观察，当条件满足，获取到了同步状态，就可以从这个自旋过程中退出，否则依旧留在这个自旋过程中（这里并不会始终自旋下去，而是会阻塞当前节点的线程）。
```Java
final boolean acquireQueued(final Node node, int arg) {
    boolean failed = true;
    try {
        boolean interrupted = false;
        for (;;) {
            final Node p = node.predecessor();
            if (p == head && tryAcquire(arg)) {
                setHead(node); // 只有获取到同步状态的线程才会进行该操作
                p.next = null; // help GC
                failed = false;
                return interrupted;
            }
            // shouldParkAfterFailedAcquire()会将处于取消状态的node剔除
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                interrupted = true;
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}
private final boolean parkAndCheckInterrupt() {
	LockSupport.park(this); // 阻塞当前线程，等待首节点线程唤醒
	return Thread.interrupted();
}
```

在acquireQueued(final Node node,int arg)方法中，当前线程在“死循环”中尝试获取同步状态，而只有前驱节点是头节点才能够尝试获取同步状态，这是为什么？原因有两个，如下。
1. 头节点是成功获取到同步状态的节点，而头节点的线程释放了同步状态之后，将会唤醒其后继节点，后继节点的线程被唤醒后需要检查自己的前驱节点是否是头节点。
2. 维护同步队列的FIFO原则。

<img src="./_image/AQS 队列同步器/22-52-45.jpg"/>

由于非首节点线程前驱节点出队或者被中断而从等待状态返回，随后检查自己的前驱是否是头节点，如果是则尝试获取同步状态。可以看到节点和节点之间在循环检查的过程中基本不相互通信，而是简单地判断自己的前驱是否为头节点，这样就使得节点的释放规则符合FIFO，并且也便于对过早通知的处理（过早通知是指前驱节点不是头节点的线程由于中断而被唤醒）。

独占式同步状态获取流程，也就是acquire(int arg)方法调用流程，如图所示：

<img src="./_image/AQS 队列同步器/22-53-13.jpg"/>

获取同步状态成功的线程执行完毕后，是如何唤醒后续线程的呢？下面就来到了`lock.unlock()`流程了。调用`lock.unlock()`，会执行到`AbstractQueuedSynchronizer.release(int arg)`：
```Java
public final boolean release(int arg) {
	if (tryRelease(arg)) { // 重置同步状态state
		Node h = head;
		if (h != null && h.waitStatus != 0) // head非空并且不是处于初始化状态
			unparkSuccessor(h);
		return true;
	}
	return false;
}

protected final boolean tryRelease(int releases) {
	int c = getState() - releases;
	if (Thread.currentThread() != getExclusiveOwnerThread())
		throw new IllegalMonitorStateException();
	boolean free = false;
	if (c == 0) {
		free = true;
		setExclusiveOwnerThread(null);
	}
	setState(c);
	return free;
}

private void unparkSuccessor(Node node) {
	int ws = node.waitStatus;
	if (ws < 0)
		compareAndSetWaitStatus(node, ws, 0); // 设置node为初始化状态

	/*
	 * Thread to unpark is held in successor, which is normally
	 * just the next node.  But if cancelled or apparently null,
	 * traverse backwards from tail to find the actual
	 * non-cancelled successor.
	 */
	Node s = node.next;
	if (s == null || s.waitStatus > 0) {
		s = null;
		for (Node t = tail; t != null && t != node; t = t.prev)
			if (t.waitStatus <= 0)
				s = t;
	}
	if (s != null)
		LockSupport.unpark(s.thread);
}
```
#### 共享式同步状态获取与释放

共享式同步状态获取与释放与独占式同步状态获取与释放流程类似，以ReadWriteLock为例说明，共享式同步状态（AQS中的state的值，int类型）是32位的，前16位作为readLock的状态使用，后16位作为writeLock的状态使用。具体细节请参考ReadWriteLock源码。

**参考资料：**

1、《Java并发编程的艺术》AQS章节
