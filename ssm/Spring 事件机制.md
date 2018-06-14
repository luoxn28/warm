
Spring的Application拥有发布事件并且注册事件监听器的能力，拥有一套完整的事件发布和监听机制。在Java中，通过java.util. EventObject来描述事件，通过java.util. EventListener来描述事件监听器，在众多的框架和组件中，建立一套事件机制通常是基于这两个接口来进行扩展。

在事件机制中，一般有以下几个概念：
- **事件源**：事件产生者，事件是事件源与监听器之间传递的信息
- **事件广播器**：事件源与事件监听器的中介，当事件源发布一个事件时，由事件广播器传递给对应的事件监听器，起到解耦作用
- **事件监听器**：事件处理者

**事件使用示例**

首先定义事件、事件监听器和事件发布者。
```Java
public class LuoEvent extends ApplicationEvent {
    @Setter
    @Getter
    private String message;
 
    public LuoEvent(Object source, String message) {
        super(source);
        this.message = message;
    }
}
 
@Component
public class EventListener implements ApplicationListener<LuoEvent> {
    public void onApplicationEvent(LuoEvent event) {
        System.out.println("recv: " + event.getMessage());
    }
}
 
@Component
public class EventPublish {
    @Resource
    private ApplicationContext context;
 
    public void publish(String message) {
        context.publishEvent(new LuoEvent(this, message));
    }
}
```

然后直接调用即可：
<img src="./_image/Spring 事件机制/23-47-52.jpg"/>

注意，默认情况下，执行事件发布和事件监听都是在同一个线程里，如果想自定义一个线程池专门用于执行事件监听，则可以自定义一个applicationEventMulticaster。
<img src="./_image/Spring 事件机制/23-52-33.jpg"/>

从AbstractApplicationContext中初始化事件广播器方法initApplicationEventMulticaster可以看出，如果包含了名字为"applicationEventMulticaster"的bean实例，则用该bean作为事件广播器，否则new一个SimpleApplicationEventMulticaster实例。
```Java
// AbstractApplicationContext
public static final String APPLICATION_EVENT_MULTICASTER_BEAN_NAME = "applicationEventMulticaster";
protected void initApplicationEventMulticaster() {
    ConfigurableListableBeanFactory beanFactory = getBeanFactory();
    if (beanFactory.containsLocalBean(APPLICATION_EVENT_MULTICASTER_BEAN_NAME)) {
        this.applicationEventMulticaster =
                beanFactory.getBean(APPLICATION_EVENT_MULTICASTER_BEAN_NAME, ApplicationEventMulticaster.class);
    }
    else {
        this.applicationEventMulticaster = new SimpleApplicationEventMulticaster(beanFactory);
        beanFactory.registerSingleton(APPLICATION_EVENT_MULTICASTER_BEAN_NAME, this.applicationEventMulticaster);
    }
}
```


## 1 事件发布广播流程

从事件发布广播，到用户自定义的事件监听处理逻辑，整个流程还是比较清晰的，代码如下：
```Java
// AbstractApplicationContext
@Override
public void publishEvent(ApplicationEvent event) {
    publishEvent(event, null);
}
 
protected void publishEvent(Object event, ResolvableType eventType) {
    // Decorate event as an ApplicationEvent if necessary
    ApplicationEvent applicationEvent;
    if (event instanceof ApplicationEvent) {
        applicationEvent = (ApplicationEvent) event;
    }
    else {
        applicationEvent = new PayloadApplicationEvent<Object>(this, event);
        if (eventType == null) {
            eventType = ((PayloadApplicationEvent)applicationEvent).getResolvableType();
        }
    }
 
    // Multicast right now if possible - or lazily once the multicaster is initialized
    if (this.earlyApplicationEvents != null) {
        this.earlyApplicationEvents.add(applicationEvent);
    }
    else {
        // 事件发布
        getApplicationEventMulticaster().multicastEvent(applicationEvent, eventType);
    }
}
 
// SimpleApplicationEventMulticaster
@Override
public void multicastEvent(final ApplicationEvent event, ResolvableType eventType) {
    ResolvableType type = (eventType != null ? eventType : resolveDefaultEventType(event));
    // 获取关注对应event的所有监听器
    for (final ApplicationListener<?> listener : getApplicationListeners(event, type)) {
        // 有线程池时抛给线程池处理，否则直接在该线程进行事件处理
        Executor executor = getTaskExecutor();
        if (executor != null) {
            executor.execute(new Runnable() {
                @Override
                public void run() {
                    invokeListener(listener, event);
                }
            });
        }
        else {
            invokeListener(listener, event);
        }
    }
}
 
// SimpleApplicationEventMulticaster
protected void invokeListener(ApplicationListener listener, ApplicationEvent event) {
    try {
        // 事件监听处理，这样就到了用户自定义的事件监听逻辑了
        listener.onApplicationEvent(event);
    }
    // ...
}
```

在事件广播时，对关注该事件的所有监听器进行触发调用，那么这些监听器是如何获取的呢？是通过getApplicationListeners(event, type)来完成的，该方法主要作用就是根据事件类型，从事件检索cache中查找监听器列表，如果找不到则从系统默认的监听器列表（包含了系统定义的所有监听器）中进行检索，然后将该监听器列表存到检索cache，便于下次检索。
```Java
// AbstractApplicationEventMulticaster
protected Collection<ApplicationListener<?>> getApplicationListeners(
        ApplicationEvent event, ResolvableType eventType) {
 
    Object source = event.getSource();
    Class<?> sourceType = (source != null ? source.getClass() : null);
    ListenerCacheKey cacheKey = new ListenerCacheKey(eventType, sourceType);
 
    // 从检索缓存查找
    ListenerRetriever retriever = this.retrieverCache.get(cacheKey);
    if (retriever != null) {
        return retriever.getApplicationListeners();
    }
 
    if (this.beanClassLoader == null ||
            (ClassUtils.isCacheSafe(event.getClass(), this.beanClassLoader) &&
                    (sourceType == null || ClassUtils.isCacheSafe(sourceType, this.beanClassLoader)))) {
        // Fully synchronized building and caching of a ListenerRetriever
        synchronized (this.retrievalMutex) {
            retriever = this.retrieverCache.get(cacheKey);
            if (retriever != null) {
                return retriever.getApplicationListeners();
            }
            retriever = new ListenerRetriever(true);
             
            // 从系统默认的监听器列表查询
            Collection<ApplicationListener<?>> listeners =
                    retrieveApplicationListeners(eventType, sourceType, retriever);
            this.retrieverCache.put(cacheKey, retriever);
            return listeners;
        }
    }
    else {
        // No ListenerRetriever caching -> no synchronization necessary
        return retrieveApplicationListeners(eventType, sourceType, null);
    }
}
 
private Collection<ApplicationListener<?>> retrieveApplicationListeners(
        ResolvableType eventType, Class<?> sourceType, ListenerRetriever retriever) {
 
    LinkedList<ApplicationListener<?>> allListeners = new LinkedList<ApplicationListener<?>>();
    Set<ApplicationListener<?>> listeners;
    Set<String> listenerBeans;
    synchronized (this.retrievalMutex) {
        // 系统默认的监听器列表及其对应的beanName列表
        listeners = new LinkedHashSet<ApplicationListener<?>>(this.defaultRetriever.applicationListeners);
        listenerBeans = new LinkedHashSet<String>(this.defaultRetriever.applicationListenerBeans);
    }
    for (ApplicationListener<?> listener : listeners) {
        if (supportsEvent(listener, eventType, sourceType)) {
            if (retriever != null) {
                retriever.applicationListeners.add(listener);
            }
            allListeners.add(listener);
        }
    }
    if (!listenerBeans.isEmpty()) {
        // listenerBeans依次检索，保证所有支持该事件的beanListener都被检索到
        BeanFactory beanFactory = getBeanFactory();
        for (String listenerBeanName : listenerBeans) {
            try {
                Class<?> listenerType = beanFactory.getType(listenerBeanName);
                if (listenerType == null || supportsEvent(listenerType, eventType)) {
                    ApplicationListener<?> listener =
                            beanFactory.getBean(listenerBeanName, ApplicationListener.class);
                    if (!allListeners.contains(listener) && supportsEvent(listener, eventType, sourceType)) {
                        if (retriever != null) {
                            retriever.applicationListenerBeans.add(listenerBeanName);
                        }
                        allListeners.add(listener);
                    }
                }
            }
        }
    }
     
    // 监听器列表排序，监听器通过@Order进行优先级排序
    AnnotationAwareOrderComparator.sort(allListeners);
    return allListeners;
}
```


## 2 事件监听器注册流程

事件监听器需要被ApplicationContext收集并统一管理起来，这样事件发布时才能进行广播操作。其实事件监听器的注册流程是在ApplicationContext的初始化过程中完成的，具体是在初始化bean的postProcessAfterInitialization方法中，在该方法中首先会判断该bean是否bean instanceof ApplicationListener，如果是则掉用applicationContext.addApplicationListener((ApplicationListener<?>) bean)进行事件监听器注册操作。
```Java
// ApplicationListenerDetector
@Override
public Object postProcessAfterInitialization(Object bean, String beanName) {
    if (this.applicationContext != null && bean instanceof ApplicationListener) {
        Boolean flag = this.singletonNames.get(beanName);
        if (Boolean.TRUE.equals(flag)) {
            // singleton bean (top-level or inner): register on the fly
            this.applicationContext.addApplicationListener((ApplicationListener<?>) bean);
        }
    }
    return bean;
}
 
// AbstractApplicationContext
@Override
public void addApplicationListener(ApplicationListener<?> listener) {
    if (this.applicationEventMulticaster != null) {
        this.applicationEventMulticaster.addApplicationListener(listener);
    }
    else {
        this.applicationListeners.add(listener);
    }
}
 
// AbstractApplicationEventMulticaster
@Override
public void addApplicationListener(ApplicationListener<?> listener) {
    synchronized (this.retrievalMutex) {
        Object singletonTarget = AopProxyUtils.getSingletonTarget(listener);
        if (singletonTarget instanceof ApplicationListener) {
            this.defaultRetriever.applicationListeners.remove(singletonTarget);
        }
        // 监听器注册到applicationListeners
        this.defaultRetriever.applicationListeners.add(listener);
        this.retrieverCache.clear();
    }
}
```

**参考资料：**

> 1、Spring事件机制源码
