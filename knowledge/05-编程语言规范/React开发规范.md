---
category: 05-编程语言规范
priority: recommended
updated: 2026-05-30
---

# React 开发规范

## 概述

本文档定义 React 19 及以上的开发最佳实践，强调函数组件优先、Hooks 的正确使用、组件设计原则（单一职责、可组合性）以及状态管理的选型与使用规范。适用于所有基于 React 的前端项目（包括 Next.js App Router 项目）。

## 核心规则

### MUST（强制遵守）

#### 函数组件优先

- 全部使用函数组件，禁止使用 Class 组件。
- 使用 `function ComponentName()` 而非 `const ComponentName = () => {}` 声明组件（便于调试和 HMR）。
- 组件文件名与导出名称一致，使用 PascalCase。

```typescript
// 正确
export default function UserProfile() { ... }

// 避免（匿名函数）
export default function () { ... }
```

#### Hooks 使用规则

- 仅在组件顶层调用 Hooks，禁止在条件、循环或嵌套函数中调用。
- 自定义 Hooks 以 `use` 开头。
- 所有 Hooks 必须列在 React 官方 `use` 前缀命名约定中。

```typescript
// 正确
function UserDashboard() {
    const [user, setUser] = useState<User | null>(null);
    const handleUpdate = useCallback((data: Partial<User>) => { ... }, []);
    useEffect(() => { fetchUser().then(setUser); }, []);
    // ...
}

// 错误 - 条件中调用 Hook
function UserDashboard({ shouldFetch }: { shouldFetch: boolean }) {
    if (shouldFetch) {
        useEffect(() => { fetchUser(); }, []);  // 违反 Hooks 规则
    }
}
```

#### useEffect 依赖完整

- `useEffect` / `useMemo` / `useCallback` 的依赖数组必须完整列出所有被引用的响应式值。
- 常见 lint 规则：`react-hooks/exhaustive-deps` 必须开启且不能 suppression。

```typescript
// 正确
useEffect(() => {
    fetchUser(userId).then(setUser);
}, [userId]);

// 错误 - 缺少依赖
useEffect(() => {
    fetchUser(userId).then(setUser);
    // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);
```

#### 组件单一职责

- 每个组件应只负责一个功能领域。
- 可提取的逻辑放入独立的自定义 Hook 或工具函数。
- 大型组件拆分为更小的子组件。

```typescript
// 合理拆分
export default function OrderPage() {
    const { orders, isLoading } = useOrders();
    return (
        <PageLayout>
            <PageHeader title="我的订单" />
            {isLoading ? <Skeleton /> : <OrderList orders={orders} />}
        </PageLayout>
    );
}

// 避免 - 一个组件做所有事
export default function OrderPage() {
    const [orders, setOrders] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    // ... 几百行渲染 + 逻辑
}
```

#### Props 设计

- 组件接口使用 `interface` 或 `type` 定义，放在组件文件顶部或独立 `types.ts`。
- 使用解构 props，避免 props 变量层层传递。
- 布尔 props 命名使用 `is` / `has` / `should` 前缀。
- 回调 props 命名使用 `on` 前缀。

```typescript
interface UserCardProps {
    user: User;
    isSelected: boolean;
    onSelect: (userId: string) => void;
    className?: string;
}

export default function UserCard({
    user,
    isSelected,
    onSelect,
    className,
}: UserCardProps) {
    return (
        <div
            className={clsx(styles.card, className, { [styles.selected]: isSelected })}
            onClick={() => onSelect(user.id)}
            role="button"
            tabIndex={0}
            onKeyDown={handleKeyDown}
        >
            <Avatar src={user.avatarUrl} alt={user.displayName} size="md" />
            <UserName name={user.displayName} />
        </div>
    );
}
```

### SHOULD（建议遵守）

#### 状态管理

- 局部组件状态使用 `useState`。
- 跨组件共享状态优先使用 React Context + `useReducer`，而非直接引入外部状态库。
- 服务端状态（API 数据）使用 `React Query`（TanStack Query）或 SWR 管理自动缓存/重试。
- 全局客户端状态（如认证、主题）使用 Zustand 或 Jotai，仅在必要时引入 Redux Toolkit。
- 避免将路由路径、URL 查询参数等放入全局状态——使用 `searchParams` 或 `next/navigation` 管理。

#### 性能优化

- 列表渲染必须使用 `key`，且 key 应为稳定唯一标识（如 `id`），禁止使用数组索引。
- 大型列表使用 `react-window` 或 `@tanstack/react-virtual` 实现虚拟化渲染。
- 计算开销大的值使用 `useMemo` 缓存。
- 避免在渲染函数中创建新的对象/函数（当传入子组件 props 时）。
- 图片使用 `next/image`（Next.js）或现代 `<img>` 的 `loading="lazy"`。

```typescript
// 正确 - 稳定的 key 和 memo
function UserList({ users }: { users: User[] }) {
    return users.map(user => <UserRow key={user.id} user={user} />);
}

// 错误 - 索引作为 key
function UserList({ users }: { users: User[] }) {
    return users.map((user, index) => <UserRow key={index} user={user} />);
}
```

#### 样式方案

- 推荐使用 CSS Modules（`.module.css`）或 Tailwind CSS。
- 避免内联样式（`style={{ ... }}`）用于布局和设计系统。
- CSS-in-JS 方案（styled-components / @emotion）需团队统一决定。

#### 测试

- 组件测试使用 `@testing-library/react`，按行为而非实现测试。
- 优先测试用户可见行为（渲染、交互），而非组件内部状态。

```typescript
// 正确 - 测试用户可见行为
it("shows loading skeleton while fetching", () => {
    render(<UserProfile userId="1" />);
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
});

// 避免 - 测试实现细节
it("sets isLoading to true initially", () => {
    const { result } = renderHook(() => useUserProfile("1"));
    expect(result.current.isLoading).toBe(true);
});
```

### MAY（可选的推荐）

- 使用 Server Components（Next.js App Router）减少客户端 JavaScript 体积。
- 使用 React 19 的 `use()` Hook 直接在组件中消费 Promise。
- 使用 React 19 的 `useActionState()` 处理表单状态。
- 使用 `Suspense` 边界实现加载状态声明式管理。

## 正确示例

```typescript
import { useState, useCallback, memo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchUserPosts } from "@/api/posts";
import { PostCard } from "./PostCard";
import { PostSkeleton } from "./PostSkeleton";
import type { Post } from "@/types";

interface PostListProps {
    userId: string;
}

export function PostList({ userId }: PostListProps) {
    const { data: posts, isLoading, error } = useQuery<Post[]>({
        queryKey: ["posts", userId],
        queryFn: () => fetchUserPosts(userId),
        enabled: !!userId,
    });

    if (isLoading) {
        return <PostSkeleton count={5} />;
    }

    if (error) {
        return <ErrorMessage message="Failed to load posts" />;
    }

    if (!posts?.length) {
        return <EmptyState icon="post" message="No posts yet" />;
    }

    return (
        <section aria-label="User posts">
            {posts.map(post => (
                <PostCard key={post.id} post={post} />
            ))}
        </section>
    );
}
```

## 错误示例

```typescript
// 错误 1：Class 组件（除非维护遗留代码）
class UserProfile extends React.Component<Props, State> {
    render() {
        return <div>{this.state.user?.name}</div>;
    }
}

// 错误 2：滥用 useEffect 做计算
function OrderTotal({ items }: { items: CartItem[] }) {
    const [total, setTotal] = useState(0);
    useEffect(() => {
        setTotal(items.reduce((sum, item) => sum + item.price * item.qty, 0));
    }, [items]);  // 这完全可以用 useMemo 实现
    return <div>{total}</div>;
}
// 正确写法：
function OrderTotal({ items }: { items: CartItem[] }) {
    const total = useMemo(
        () => items.reduce((sum, item) => sum + item.price * item.qty, 0),
        [items],
    );
    return <div>{total}</div>;
}

// 错误 3：setState 依赖旧值没有用函数式更新
function Counter() {
    const [count, setCount] = useState(0);
    const increment = () => {
        setCount(count + 1);
        setCount(count + 1);  // 两次设置使用同一个 count 值，结果只 +1
    };
}

// 错误 4：在渲染中创建新的内联函数（传递给子组件时）
function Parent() {
    return <Child onClick={() => handleClick()} />;  // 每次渲染创建新函数 -> 子组件无法 memo 优化
}
// 正确写法：
function Parent() {
    const handleClick = useCallback(() => { ... }, []);
    return <Child onClick={handleClick} />;
}

// 错误 5：Props drilling 过深
function Page({ user, onUpdateUser, onDeleteUser, isDarkMode, onToggleTheme, ... }) {
    return (
        <Header user={user} onUpdateUser={onUpdateUser} isDarkMode={isDarkMode} onToggleTheme={onToggleTheme} />
        <Main user={user} onUpdateUser={onUpdateUser} onDeleteUser={onDeleteUser} />
    );
}

// 错误 6：使用索引作为 key
{items.map((item, i) => <ListItem key={i} item={item} />)}

// 错误 7：过度嵌套的 JSX
function ComplexPage() {
    return (
        <div>
            <div>
                <div>
                    <div>  <!-- 避免超过 3 层嵌套 -->
                        Content
                    </div>
                </div>
            </div>
        </div>
    );
}
```

## 工具链配置

### ESLint React 插件

```json
{
    "extends": [
        "plugin:react/recommended",
        "plugin:react-hooks/recommended",
        "plugin:jsx-a11y/recommended"
    ],
    "rules": {
        "react/react-in-jsx-scope": "off",
        "react/prop-types": "off",
        "react/jsx-no-target-blank": "error",
        "react-hooks/rules-of-hooks": "error",
        "react-hooks/exhaustive-deps": "error",
        "react/jsx-key": ["error", { "checkFragmentShorthand": true }],
        "jsx-a11y/alt-text": "error",
        "jsx-a11y/click-events-have-key-events": "warn"
    }
}
```

### tsconfig.json（React 相关）

```json
{
    "compilerOptions": {
        "jsx": "react-jsx",
        "jsxImportSource": "react"
    }
}
```

## 参考来源

- [React 19 Documentation](https://react.dev/blog/2024/12/05/react-19)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [React Query (TanStack Query) Best Practices](https://tanstack.com/query/latest/docs/react/community/tkdodos-blog)
- [React Testing Library Guiding Principles](https://testing-library.com/docs/guiding-principles)
- [Next.js App Router Documentation](https://nextjs.org/docs/app)
- [Kent C. Dodds – Inversion of Control](https://kentcdodds.com/blog/inversion-of-control)
