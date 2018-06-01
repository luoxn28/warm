Java lambda 一眼看上去有点像匿名内部类的简化形式，但是二者确有着本质的差别。匿名内部类经编译后会生成对应的class文件，格式为`XXX$n.class`；而lambda代码经过编译后生成一个private方法，方法名格式为`lambda$main$n`。

```Java
// Application.main 方法中代码
ArrayList<String> list = CollectionUtil.newArrayList("I", "love", "you");
list.forEach(new Consumer<String>() {
    @Override
    public void accept(String s) {
        System.out.println(s);
    }
});
list.forEach(System.out::println);
```
以上代码就会产生一个Application$1.class文件和一个lambda$main$0的方法。既然lambda实现不是内部类，那么在lambda中this就代表的当前所在类实例。
```Java
// Application.main 方法中代码
ArrayList<String> list = CollectionUtil.newArrayList("I", "love", "you");
list.forEach(item -> {
    System.out.println(item);
});
```

通过javap -c -p Application.class查看以上代码对应的字节码：
```Java
Constant pool:
   #1 = Methodref          #12.#36        // java/lang/Object."<init>":()V
   #2 = Class              #37            // java/lang/String
   #3 = String             #38            // I
   #4 = String             #39            // love
   #5 = String             #40            // you
   #6 = Methodref          #41.#42        // cn/hutool/core/collection/CollectionUtil.newArrayList:([Ljava/lang/Object;)Ljava/util/ArrayList;
   #7 = InvokeDynamic      #0:#48         // #0:accept:()Ljava/util/function/Consumer;
   #8 = Methodref          #49.#50        // java/util/ArrayList.forEach:(Ljava/util/function/Consumer;)V
   #9 = Fieldref           #51.#52        // java/lang/System.out:Ljava/io/PrintStream;
  #10 = Methodref          #53.#54        // java/io/PrintStream.println:(Ljava/lang/String;)V
  #11 = Class              #55            // com/luo/demo/Application
  #12 = Class              #56            // java/lang/Object
  #13 = Utf8               <init>
  #14 = Utf8               ()V
  #15 = Utf8               Code
  #16 = Utf8               LineNumberTable
  #17 = Utf8               LocalVariableTable
  #18 = Utf8               this
  #19 = Utf8               Lcom/luo/demo/Application;
  #20 = Utf8               main
  #21 = Utf8               ([Ljava/lang/String;)V
  #22 = Utf8               args
  #23 = Utf8               [Ljava/lang/String;
  #24 = Utf8               list
  #25 = Utf8               Ljava/util/ArrayList;
  #26 = Utf8               LocalVariableTypeTable
  #27 = Utf8               Ljava/util/ArrayList<Ljava/lang/String;>;
  #28 = Utf8               lambda$main$0
  #29 = Utf8               (Ljava/lang/String;)V
  #30 = Utf8               item
  #31 = Utf8               Ljava/lang/String;
  #32 = Utf8               SourceFile
  #33 = Utf8               Application.java
  #34 = Utf8               RuntimeVisibleAnnotations
  #35 = Utf8               Lorg/springframework/boot/autoconfigure/SpringBootApplication;
  #36 = NameAndType        #13:#14        // "<init>":()V
  #37 = Utf8               java/lang/String
  #38 = Utf8               I
  #39 = Utf8               love
  #40 = Utf8               you
  #41 = Class              #57            // cn/hutool/core/collection/CollectionUtil
  #42 = NameAndType        #58:#59        // newArrayList:([Ljava/lang/Object;)Ljava/util/ArrayList;
  #43 = Utf8               BootstrapMethods
  #44 = MethodHandle       #6:#60         // invokestatic java/lang/invoke/LambdaMetafactory.metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
  #45 = MethodType         #61            //  (Ljava/lang/Object;)V
  #46 = MethodHandle       #6:#62         // invokestatic com/luo/demo/Application.lambda$main$0:(Ljava/lang/String;)V
  #47 = MethodType         #29            //  (Ljava/lang/String;)V
  #48 = NameAndType        #63:#64        // accept:()Ljava/util/function/Consumer;
  #49 = Class              #65            // java/util/ArrayList
  #50 = NameAndType        #66:#67        // forEach:(Ljava/util/function/Consumer;)V
  #51 = Class              #68            // java/lang/System
  #52 = NameAndType        #69:#70        // out:Ljava/io/PrintStream;
  #53 = Class              #71            // java/io/PrintStream
  #54 = NameAndType        #72:#29        // println:(Ljava/lang/String;)V
  #55 = Utf8               com/luo/demo/Application
  #56 = Utf8               java/lang/Object
  #57 = Utf8               cn/hutool/core/collection/CollectionUtil
  #58 = Utf8               newArrayList
  #59 = Utf8               ([Ljava/lang/Object;)Ljava/util/ArrayList;
  #60 = Methodref          #73.#74        // java/lang/invoke/LambdaMetafactory.metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
  #61 = Utf8               (Ljava/lang/Object;)V
  #62 = Methodref          #11.#75        // com/luo/demo/Application.lambda$main$0:(Ljava/lang/String;)V
  #63 = Utf8               accept
  #64 = Utf8               ()Ljava/util/function/Consumer;
  #65 = Utf8               java/util/ArrayList
  #66 = Utf8               forEach
  #67 = Utf8               (Ljava/util/function/Consumer;)V
  #68 = Utf8               java/lang/System
  #69 = Utf8               out
  #70 = Utf8               Ljava/io/PrintStream;
  #71 = Utf8               java/io/PrintStream
  #72 = Utf8               println
  #73 = Class              #76            // java/lang/invoke/LambdaMetafactory
  #74 = NameAndType        #77:#81        // metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
  #75 = NameAndType        #28:#29        // lambda$main$0:(Ljava/lang/String;)V
  #76 = Utf8               java/lang/invoke/LambdaMetafactory
  #77 = Utf8               metafactory
  #78 = Class              #83            // java/lang/invoke/MethodHandles$Lookup
  #79 = Utf8               Lookup
  #80 = Utf8               InnerClasses
  #81 = Utf8               (Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
  #82 = Class              #84            // java/lang/invoke/MethodHandles
  #83 = Utf8               java/lang/invoke/MethodHandles$Lookup
  #84 = Utf8               java/lang/invoke/MethodHandles
{
  public com.luo.demo.Application();
    descriptor: ()V
    flags: ACC_PUBLIC
    Code:
      stack=1, locals=1, args_size=1
         0: aload_0
         1: invokespecial #1                  // Method java/lang/Object."<init>":()V
         4: return
      LineNumberTable:
        line 12: 0
      LocalVariableTable:
        Start  Length  Slot  Name   Signature
            0       5     0  this   Lcom/luo/demo/Application;
 
  public static void main(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)V
    flags: ACC_PUBLIC, ACC_STATIC
    Code:
      stack=4, locals=2, args_size=1
         0: iconst_3
         1: anewarray     #2                  // class java/lang/String
         4: dup
         5: iconst_0
         6: ldc           #3                  // String I
         8: aastore
         9: dup
        10: iconst_1
        11: ldc           #4                  // String love
        13: aastore
        14: dup
        15: iconst_2
        16: ldc           #5                  // String you
        18: aastore
        19: invokestatic  #6                  // Method cn/hutool/core/collection/CollectionUtil.newArrayList:([Ljava/lang/Object;)Ljava/util/ArrayList;
        22: astore_1
        23: aload_1
        24: invokedynamic #7,  0              // InvokeDynamic #0:accept:()Ljava/util/function/Consumer;
        29: invokevirtual #8                  // Method java/util/ArrayList.forEach:(Ljava/util/function/Consumer;)V
        32: return
      LineNumberTable:
        line 15: 0
        line 16: 23
        line 19: 32
      LocalVariableTable:
        Start  Length  Slot  Name   Signature
            0      33     0  args   [Ljava/lang/String;
           23      10     1  list   Ljava/util/ArrayList;
      LocalVariableTypeTable:
        Start  Length  Slot  Name   Signature
           23      10     1  list   Ljava/util/ArrayList<Ljava/lang/String;>;
 
  private static void lambda$main$0(java.lang.String);
    descriptor: (Ljava/lang/String;)V
    flags: ACC_PRIVATE, ACC_STATIC, ACC_SYNTHETIC
    Code:
      stack=2, locals=1, args_size=1
         0: getstatic     #9                  // Field java/lang/System.out:Ljava/io/PrintStream;
         3: aload_0
         4: invokevirtual #10                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
         7: return
      LineNumberTable:
        line 17: 0
        line 18: 7
      LocalVariableTable:
        Start  Length  Slot  Name   Signature
            0       8     0  item   Ljava/lang/String;
}
```

通过字节码可以看出，调用lambda方法时使用了`invokedynamic`，该字节码命令是为了支持动态语言特性而在Java7中新增的。Java的lambda表达式实现上也就借助于`invokedynamic`命令。

字节码中每一处含有invokeDynamic指令的位置都称为**动态调用点**，这条指令的第一个参数不再是代表方法调用符号引用的CONSTANT_Methodref_info常亮，而是变成为JDK7新加入的CONSTANT_InvokeDynamic_info常量，从这个新常量中可得到3项信息：引导方法（Bootstrap Method，此方法存放在新增的BootstrapMethods属性中）、方法类型和名称。引导方法是有固定的参数，并且返回值是java.lang.invoke.CallSite对象，这个代表真正要执行的目标方法调用。根据CONSTANT_InvokeDynamic_info常量中提供的信息，虚拟机可以找到并执行引导方法，从而获得一个CallSite对象，最终调用要执行的目标方法。

从上述mian方法的字节码可见，有一个invokeDynamic指令，他的参数为第7项常量（第二个值为0的参数HotSpot中用不到，占位符）。
`invokedynamic #7,  0              // InvokeDynamic #0:accept:()Ljava/util/function/Consumer;`

常量池中第7项是`#7 = InvokeDynamic      #0:#48         // #0:accept:()Ljava/util/function/Consumer;`，说明它是一项CONSTANT_InvokeDynamic_info常量，常量值中前面的#0表示引导方法取BootstrapMethods属性表的第0项，而后面的#48表示引用第48项类型为CONSTANAT_NameAndType_info的常量，从这个常量中可以获取方法名称和描述符，即accept方法。

```Java
BootstrapMethods:
  0: #44 invokestatic java/lang/invoke/LambdaMetafactory.metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #45 (Ljava/lang/Object;)V
      #46 invokestatic com/luo/demo/Application.lambda$main$0:(Ljava/lang/String;)V
      #47 (Ljava/lang/String;)V
```

<img src="./_image/Java Lambda 原理/clipboard.png"/>

上图是在lambda代码中打断点时的调用栈信息，如果在这里的lambda中打印当前所属class，就是Application类，也印证了前面分析的lambda代码会生成一个private方法。

从调用栈的信息来看，是在accept方法中调用lambda对应的private方法（ambda$main$0）的，但是这里的accept方法是属于什么对象呢？从图中看是一串数字字符串，这里可以理解成一个Consumer接口的实现类即可，每个lambda表达式可以理解成在一个新的Consumer实现类中调用的即可。使用命令jmap -histo查看JVM进程类和对象信息可以看到这一行信息：
`600:             1             16  com.luo.demo.Application$$Lambda$5/1615039080`

**参考资料：**

1、[https://blog.csdn.net/zxhoo/article/details/38387141](https://blog.csdn.net/zxhoo/article/details/38387141)
