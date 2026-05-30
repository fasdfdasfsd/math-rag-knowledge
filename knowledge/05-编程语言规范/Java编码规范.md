---
category: 05-编程语言规范
priority: recommended
updated: 2026-05-30
---

# Java 编码规范

## 概述

本文档定义 Java 项目的编码标准，以 Google Java Style Guide 为核心基础，结合阿里巴巴 Java 开发手册的关键最佳实践，适用于团队所有 Java 后端服务开发。

## 核心规则

### MUST（强制遵守）

#### 源文件结构

- 文件编码：UTF-8。
- 许可证或版权信息位于文件顶部注释块。
- package 语句不换行，import 语句不换行。
- import 分组顺序：
  1. 所有静态 import 为一组。
  2. `com.google` / `com.alibaba` / `org.springframework` 等公司/框架 import。
  3. 第三方库 import。
  4. 顶级项目 import。
  - 每组间空一行，组内按字母序排列。
  - 禁止使用 `import *`。

#### 命名规范

| 元素 | 风格 | 示例 |
|------|------|------|
| 类 / 接口 | UpperCamelCase | `UserService`, `OrderRepository` |
| 方法 | lowerCamelCase | `getUserById()`, `saveOrder()` |
| 变量 | lowerCamelCase | `userName`, `orderList` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_TIMES`, `DEFAULT_PAGE_SIZE` |
| 枚举 | UpperCamelCase（类级），UPPER_SNAKE_CASE（枚举值） | `enum Color { RED, GREEN, BLUE }` |
| 包名 | 全小写，点分隔 | `com.company.module.service` |
| 抽象类 | 建议以 `Abstract` 开头或 `Base` 结尾 | `AbstractBaseController` |
| 异常类 | 以 `Exception` 结尾 | `OrderNotFoundException` |
| 测试类 | 以 `Test` 结尾 | `UserServiceTest` |

#### 大括号

- 大括号使用 Egyptian 风格（左大括号前不换行）。
- 空代码块内可以紧凑写作 `{}`。
- `if` / `else` / `for` / `while` 即使只有一行也需要大括号。

```java
// 正确
if (user == null) {
    throw new UserNotFoundException();
}

// 错误 - 缺少大括号
if (user == null)
    throw new UserNotFoundException();
```

#### 缩进与行长

- 缩进：4 个空格，禁止使用 Tab。
- 行长度：最大 120 字符。
- 换行：运算符放在新行开头，. 成员访问也放在新行开头。

#### 异常处理

- 禁止捕获通用的 `Exception` / `RuntimeException` / `Throwable`，除非在顶层框架级代码。
- 异常需有具体业务含义，推荐自定义业务异常。
- 不要在 finally 块中 return 或 throw。
- 资源使用 try-with-resources 自动关闭。

```java
// 正确
try (Connection conn = dataSource.getConnection();
     PreparedStatement stmt = conn.prepareStatement(sql)) {
    stmt.setString(1, userId);
    return stmt.executeQuery();
} catch (SQLException e) {
    throw new DataAccessException("Failed to query user: " + userId, e);
}

// 错误 - 捕获过于宽泛
try {
    processOrder(orderId);
} catch (Exception e) {
    logger.error("Failed", e);
}
```

#### 集合使用

- 必须指定泛型类型。
- 优先使用 `List.of()`、`Set.of()`、`Map.of()` 创建不可变集合。
- 使用 `Map.forEach()` 替代传统 entrySet 遍历。
- 使用 `Collection.isEmpty()` 而非 `size() == 0`。
- 预计元素数量时指定初始容量。

#### Optional 使用规范（Spring Framework / JDK 中）

- 禁止将 `Optional` 作为字段类型或方法参数类型。
- 仅在方法返回类型使用 `Optional` 表示可能为空的结果。
- 禁止对 `Optional` 调用 `get()` 前不检查 `isPresent()`。

### SHOULD（建议遵守）

- 类成员变量访问级别：优先 private，需要时 protected，谨慎 public。
- 方法参数数量不超过 4 个，超过时考虑封装参数对象。
- 避免过长的方法体（超过 80 行建议拆分）。
- 覆写方法统一使用 `@Override` 注解。
- 使用 Lombok 减少样板代码（`@Data`, `@Builder`, `@Slf4j` 等）。
- 使用 SLF4J 门面日志，参数化占位符，避免字符串拼接。
- equals() 和 hashCode() 必须同时覆写。

### MAY（可选的推荐）

- 项目使用 Java 17+ 时，优先使用 `record` 定义不可变数据载体。
- 使用 `sealed class` 限制继承层次。
- 使用 `var` 局部变量推断（仅限右侧类型明确时）。

## 正确示例

```java
package com.example.order.service;

import com.example.order.entity.Order;
import com.example.order.repository.OrderRepository;
import com.example.order.exception.OrderNotFoundException;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Service for managing orders.
 *
 * <p>Handles order creation, status updates, and retrieval operations.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class OrderService {

    private static final int MAX_RETRY_COUNT = 3;

    private final OrderRepository orderRepository;

    /**
     * Retrieves an order by its unique identifier.
     *
     * @param orderId the order ID
     * @return the found order
     * @throws OrderNotFoundException if no order with the given ID exists
     */
    public Order getOrderById(String orderId) {
        return orderRepository.findById(orderId)
                .orElseThrow(() -> {
                    log.warn("Order not found: {}", orderId);
                    return new OrderNotFoundException("Order not found: " + orderId);
                });
    }

    /**
     * Retrieves all orders for a specific user within a date range.
     *
     * @param userId    the user ID
     * @param startDate range start (inclusive)
     * @param endDate   range end (exclusive)
     * @return list of orders (never null)
     */
    public List<Order> getUserOrders(String userId, LocalDateTime startDate, LocalDateTime endDate) {
        return orderRepository.findByUserIdAndCreatedAtBetween(userId, startDate, endDate);
    }

    /**
     * Creates a new order with pending status.
     *
     * @param order the order to create (without ID)
     * @return the persisted order with generated ID
     */
    @Transactional
    public Order createOrder(Order order) {
        order.setStatus(Order.Status.PENDING);
        order.setCreatedAt(LocalDateTime.now());
        Order saved = orderRepository.save(order);
        log.info("Order created: id={}, userId={}", saved.getId(), saved.getUserId());
        return saved;
    }
}
```

## 错误示例

```java
// 错误 1：命名不规范
class order_service {            // 类名应为 UpperCamelCase
    String UserName;             // 字段应为 lowerCamelCase
    final int MAX_RETRY = 3;     // 常量命名正确，但如果不是常量则应为小写
}

// 错误 2：magic number
public double calculate(double price) {
    return price * 0.95;         // 0.95 含义不明，应定义为常量
}
// 正确写法：
private static final double DISCOUNT_RATE = 0.95;
public double calculate(double price) {
    return price * DISCOUNT_RATE;
}

// 错误 3：捕获过于宽泛的异常
try {
    executeQuery();
} catch (Exception e) {          // 应捕获具体异常类型
    throw e;
}

// 错误 4：equals 时常量放变量后面
if (user.getStatus().equals("ACTIVE")) {  // user.getStatus() 可能为 null → NPE
    // ...
}
// 正确写法：
if ("ACTIVE".equals(user.getStatus())) {
    // ...
}

// 错误 5：线程不安全 SimpleDateFormat
private static final SimpleDateFormat FORMAT = new SimpleDateFormat("yyyy-MM-dd");
// 应使用 DateTimeFormatter（线程安全）
private static final DateTimeFormatter FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd");

// 错误 6：在循环中拼接字符串
String result = "";
for (int i = 0; i < 1000; i++) {
    result += item;              // 产生大量中间 String 对象
}
// 正确写法：使用 StringBuilder
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 1000; i++) {
    sb.append(item);
}
String result = sb.toString();

// 错误 7：Optional 不规范使用
public class User {
    private Optional<String> email;  // Optional 不应作为字段类型
}

public void process(Optional<String> name) {  // Optional 不应作为参数类型
    String value = name.get();                // 未检查 isPresent()
}

// 错误 8：方法过长
public void processOrder(String orderId) {
    // 200 行逻辑 - 应拆分为多个小方法
    // ...
}
```

## 工具链配置

### Checkstyle（Google Style）

`checkstyle.xml` 部分关键配置：

```xml
<?xml version="1.0"?>
<!DOCTYPE module PUBLIC
    "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
    "https://checkstyle.org/dtds/configuration_1_3.dtd">
<module name="Checker">
    <module name="TreeWalker">
        <module name="UnusedImports"/>
        <module name="RedundantImport"/>
        <module name="ConstantName"/>
        <module name="LocalFinalVariableName"/>
        <module name="LocalVariableName"/>
        <module name="MemberName"/>
        <module name="MethodName"/>
        <module name="PackageName"/>
        <module name="ParameterName"/>
        <module name="StaticVariableName"/>
        <module name="TypeName"/>
        <module name="LineLength">
            <property name="max" value="120"/>
        </module>
        <module name="EmptyBlock"/>
        <module name="NeedBraces"/>
        <module name="LeftCurly"/>
        <module name="RightCurly"/>
        <module name="WhitespaceAround"/>
        <module name="GenericWhitespace"/>
    </module>
    <module name="FileLength">
        <property name="max" value="2000"/>
    </module>
</module>
```

### Maven / Gradle 插件配置

**Maven (pom.xml):**

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-checkstyle-plugin</artifactId>
    <version>3.3.1</version>
    <configuration>
        <configLocation>checkstyle.xml</configLocation>
        <failsOnError>true</failsOnError>
    </configuration>
</plugin>
```

**Gradle (build.gradle):**

```groovy
checkstyle {
    toolVersion = '10.12.7'
    configFile = rootProject.file('config/checkstyle/checkstyle.xml')
}
```

## 参考来源

- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- [阿里巴巴 Java 开发手册 (华山版)](https://github.com/alibaba/p3c)
- [Effective Java (3rd Edition) – Joshua Bloch](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/)
- [Checkstyle Documentation](https://checkstyle.sourceforge.io/)
- [Spring Framework Coding Style](https://github.com/spring-projects/spring-framework/wiki/Spring-Framework-Coding-Style)
