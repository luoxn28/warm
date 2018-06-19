
## IoC基础

Spring是一个轻量级的Java开发框架，其提供的两大基础功能为IoC和AOP，其中IoC为依赖反转（Inversion of Control）。IOC容器的基本理念就是“为别人服务”，那为别人服务什么呢？其中最重要就是业务对象的构建管理和业务对象之间的依赖绑定。
- 业务对象的构建管理：业务场景中，无需关心业务对象如何创建、如何管理，在需要时只需获取即可。业务对象的构建管理交给IoC容器，避免这部分代码对业务逻辑的侵染。
- 业务对象间的依赖绑定：IoC容器需要先了解业务对象之间的依赖关系，这样依据之前业务对象的构建管理就可以对外提供IoC服务，保证每个业务对象在使用时处于就绪状态。

IoC容器管理业务对象，首先需要知道业务对象之间的依赖关系，以下有几种方式告诉IoC容器其管理的对象之间的绑定关系：
- 可以通过简单的文本方式记录被注入对象和其依赖对象的对应关系。
- 使用描述性更强的XML文件格式记录对象之间的对应关系。
- 还可以通过编写代码的方式（调用IoC容器提供的对应API）设置对象之间的关系。
- ...

注意：不管是什么方式来告知IoC容器对象之间的绑定关系，最终都是通过编码方式（调用IOC提供的API）来将这些信息"写入"到IoC容器中的。

#### 2种基本的IoC容器类型

Spring的IoC容器提供两种基本的容器类型：`BeanFactory`和`ApplicationContext`。

- BeanFactory：基础类型IoC容器，提供基本的容器服务，如果没有特殊指定，采用延迟初始化策略，也就是当客户端需要容器中某个对象时，才对该受管理的对象初始化及其依赖注入操作。所以，相对来说，BeanFactory容器启动较快，所需资源有限，对于资源有限，并且功能要求不严格的场景，使用BeanFactory容器是比较合适的。
- ApplicationContext：ApplicationContext是在BeanFactory基础之上构建的，是一个比较高级的容器，除了拥有BeanFactory的全部功能外，也提供其他高级特性，比如事件发布、国际化信息支持等。ApplicationContext所管理的对象，默认ApplicationContext启动之后全部初始化并绑定完成，所以其启动较慢，占用资源较多。在系统资源充足，并需要提供较多功能的使用场景，ApplicationContext是一个不错的选择。

依赖注入方式有构造方法注入、属性注入和接口方法注入。依赖注入使用反射创建bean，除了这种方式之外，还可以通过静态方法创建bean，示例方法如下：
```Java
public static Hello createHello() {
    return new Hello();
}
<bean id="hello" class="com.luoxn28.Hello" factory-method="createHello">
</bean>
```

#### FactoryBean

Spring 中有两种类型的 Bean， 一种是普通Bean，另一种是工厂Bean，即FactoryBean。工厂Bean 跟普通Bean不同,，其返回的对象不是指定类的一个实例，其返回的是该工厂 Bean 的 getObject 方法所返回的对象。
FactoryBean接口源码如下所示：
```Java
public interface FactoryBean<T> {
    // 返回的实例
    T getObject() throws Exception;
    // 返回的类型
    Class<?> getObjectType();
    // 是否为单例
    boolean isSingleton();
}
```

什么时候会使用FactoryBean呢，当需要自定义Bean对象的实例化过程时使用，FactoryBean返回创建好的对象实例，这个对象是否是单例有FactoryBean内部保证。
```Java
public class Hello {
    private String name;
    private int age;
    // set/get方法
}
 
public class HelloBeanFactory implements FactoryBean<Hello> {
    @Override
    public Hello getObject() throws Exception {
        Hello hello = new Hello();
 
        hello.setName("luoxn28");
        hello.setAge(23);
        return hello;
    }
 
    @Override
    public Class<?> getObjectType() {
        return Hello.class;
    }
 
    @Override
    public boolean isSingleton() {
        return true;
    }
}
```

## Bean的注册和加载

Spring中的每个bean定义首先会被解析为一个个BeanDefinition定义，然后在按照<beanName, beanDefinition>格式存储到beanDefinitionMap中。BeanDefinition接口有多种实现类，比如对应注解类型的Bean或者xml配置类型的GenericBeanDefinition。

<img src="./_image/深入浅出Spring IoC/20-53-08.jpg"/>

由上图看出，BeanDefinition包含的信息是不是挺熟悉的， 例如类名、scope、属性、构造函数参数列表、依赖的bean、是否是单例类、是否是懒加载等，其实就是将Bean的定义信息存储到这个BeanDefinition相应的属性中，后面对Bean的操作就直接对BeanDefinition进行，例如拿到这个BeanDefinition后，可以根据里面的类名、构造函数、构造函数参数，使用反射进行对象创建。

BeanDefinition是一个接口，是一个抽象的定义，实际使用的是其实现类，如ChildBeanDefinition、RootBeanDefinition、GenericBeanDefinition等。BeanDefinition继承了AttributeAccessor，说明它具有处理属性的能力；BeanDefinition继承了BeanMetadataElement，说明它可以持有Bean元数据元素，作用是可以持有XML文件的一个bean标签对应的Object。

注意，在解析存储BeanDefinition类时并不会对BeanDefinition实际表示的类进行类加载操作，只有在创建BeanDefinition实际表示的类实例时才进行类加载和初始化操作，这里可以分别看下`注册BeanDefinition`时和`创建bean实例`时的调用栈信息：

<img src="./_image/深入浅出Spring IoC/21-02-36.jpg"/>

#### bean的解析注册

Spring中的bean实例是保存在BeanRegistry中的，bean的解析注册流程是在BeanFactory的初始化流程中完成的，比如ApplicationContext的refresh方法完成的主要流程如下：
1. 初始化前的准备工作，例如对系统属性和环境变量进行准备和验证。
2. 初始化BeanFactory，并进行XML文件的读取。
3. 对BeanFactory进行各种功能填充。
4. 子类覆盖方法做额外的处理。
5. 激活各种BeanFactory处理器。
6. 注册拦截Bean创建的Bean处理器，这里只是注册，真正的调用是在getBean的时候。
7. 为上下文初始化Message源，国际化处理。
8. 初始化应用消息广播器，并放入"applicationEventMulticaster"bean中。
9. 初始化特定上下文的bean。
10. 在所有注册的bean中查找listener bean，注册到消息广播器中。
11. 初始化剩下的单实例（no-lazy）。
12. 完成刷新过程，通知lifecycleProcessor刷新过程，同时发出ContextRefreshEvent通知别人。

ApplicationContext中bean的创建过程中，如果该类的属性是其他类，比如一个类A，A中有一个类型为B的属性b，这时在创建A的bean过程中会进行创建B的bean的操作，这里的流程是：首先完成类A的加载、连接（验证/准备/解析）、初始化，初始化完成之后进行类A属性值的初始化，发现有一个类B属性b，这时就会进行类B的加载、连接（验证/准备/解析）、初始化，接着进行B属性的初始化，完成后就创建了一个B对象b；然后继续进行类A属性b的初始化，完成后就创建了一个类A的bean了。

从上面分析可以看出，类型依赖导致的类加载解析是递归进行的，这里可以想象这样一个场景，如果类A依赖B，B又依赖C，C又依赖...，如果依赖关系达到好几百，我们都知道默认Java栈深度是有限的，假如是1000，这样肯定是要爆栈的呀 : )

#### bean的获取操作

bean的获取通过getBean来完成，`getBean -> doGetBean`方法的流程如下：
1. 转换对应的beanName，传入的name可能是beanName，也可能是别名，也可能是FactoryBean，所以需要首先转换。
2. 尝试从缓存中加载单例，单例在Spring的同一个容器中只会被创建一次，后续再获取bean，就直接从单例缓存种获取。注，如果bean是FactoryBean类型的，则会调用其getObject方法。
3. 执行 prototype 类型依赖检查，防止循环依赖。只有在单例情况下才会尝试解决循环依赖。
4. 如果当前 beanFactory 中不存在需要的 bean，则尝试从 parentBeanFactory 中获取。
5. 将之前解析过程返得到的 GenericBeanDefinition 对象合并为 RootBeanDefinition 对象，便于后续处理。
6. 如果存在依赖的 bean，则递归加载依赖的 bean。
7. 依据当前 bean 的作用域对 bean 进行实例化。
8. 如果对返回 bean 类型有要求，则进行检查，按需做类型转换。
9. 返回 bean 实例。

