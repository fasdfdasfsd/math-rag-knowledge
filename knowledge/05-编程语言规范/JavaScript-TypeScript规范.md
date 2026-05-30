---
category: 05-编程语言规范
priority: recommended
updated: 2026-05-30
---

# JavaScript / TypeScript 编码规范

## 概述

本文档定义前端和 Node.js 项目的 TypeScript 编码规范，核心参考 Airbnb JavaScript Style Guide，结合 TypeScript 严格模式最佳实践。所有项目均需使用 ESLint + Prettier 进行统一检查和格式化。

## 核心规则

### MUST（强制遵守）

#### 语言特性

- **禁止使用 `var`**，统一使用 `const`（首选）和 `let`。
- 优先使用箭头函数 `() => {}` 而非 `function` 关键字声明回调函数。
- 使用模板字符串 `` `${name}` `` 替代字符串拼接。
- 使用对象的属性简写语法。
- 使用解构赋值（对象和数组）。

```typescript
// 正确
const name = "Alice";
const greeting = `Hello, ${name}!`;
const user = { id: 1, name };
const { id, email } = user;

// 错误
var name = "Alice";              // 使用 var
const greeting = "Hello, " + name;  // 字符串拼接
const user = { id: 1, name: name }; // 未使用简写
```

#### TypeScript 严格模式

`tsconfig.json` 必须开启以下选项：

```json
{
    "compilerOptions": {
        "strict": true,
        "noUncheckedIndexedAccess": true,
        "noImplicitReturns": true,
        "noFallthroughCasesInSwitch": true,
        "exactOptionalPropertyTypes": false,
        "forceConsistentCasingInFileNames": true,
        "skipLibCheck": true
    }
}
```

- 禁止使用 `any`，优先使用 `unknown` 并在使用时进行类型收窄。
- 函数必须显式标注返回类型（尤其是公开 API）。
- 接口（interface）命名以 `I` 为前缀**不强制**，但项目内应保持一致。
- 类型（type）优先于接口用于联合类型/交叉类型。

#### 模块与导入

- 使用 ES Module (`import` / `export`)，禁止使用 CommonJS (`require` / `module.exports`)。
- 导入语句分组：
  1. 外部依赖（`react`, `lodash` 等）
  2. 内部模块（`@/components/*` 等）
  3. 样式/资源文件（`.css`, `.svg` 等）
- 禁止默认导出（default export）匿名对象——每个模块应当有具名导出或在默认导出时绑定具名标识符。

```typescript
// 推荐
export function getUser() { ... }
export const API_URL = "https://api.example.com";

// 可接受的具名默认导出
export default function UserList() { ... }

// 不推荐 - 匿名对象默认导出
export default { getUser, API_URL };
```

#### 异步编程

- 优先使用 `async` / `await` 替代裸 Promise `.then()` / `.catch()`。
- 避免 `async` 函数内遗漏 `await`。
- 使用 `Promise.all()` 或 `Promise.allSettled()` 处理并发异步操作。

```typescript
// 正确
async function fetchUserData(userId: string): Promise<User> {
    const [profile, posts] = await Promise.all([
        fetchProfile(userId),
        fetchPosts(userId),
    ]);
    return { ...profile, posts };
}

// 错误
function fetchUserData(userId: string): Promise<User> {
    let profile, posts;
    return fetchProfile(userId).then(p => {
        profile = p;
        return fetchPosts(userId);
    }).then(p => {
        posts = p;
        return { ...profile, posts };
    });
}
```

#### null / undefined 处理

- 使用可选链 `?.` 和空值合并 `??`。
- 禁止使用 `||` 作为默认值语义（会过滤 `false` / `0` / `""`）。

```typescript
// 正确
const displayName = user?.profile?.name ?? "Anonymous";

// 错误
const displayName = user.profile.name || "Anonymous";  // 如果 name 为空字符串会错误替换
```

### SHOULD（建议遵守）

- 数组回调使用 `map()` / `filter()` / `reduce()` / `find()` 等函数式方法，避免使用 `for` 循环。
- 使用 `for...of` 而非 `for...in` 遍历数组。
- 布尔值变量命名使用 `is` / `has` / `should` 前缀（如 `isLoading`, `hasError`）。
- 事件处理函数命名以 `handle` 前缀（如 `handleSubmit`, `handleClick`）。
- 组件文件使用 `.tsx` 扩展名，纯逻辑文件使用 `.ts` 扩展名。
- 使用 `ReadonlyArray<T>` 或 `readonly` 修饰符声明不可变数组参数。
- 写测试时使用 `vitest` 或 `jest`，测试文件与被测文件同目录，命名为 `*.test.ts`。

### MAY（可选的推荐）

- 使用 `satisfies` 操作符在保留类型推断的同时进行类型约束（TypeScript 4.9+）。
- 使用 `const` 断言 `as const` 声明字面量类型。
- 使用 `never` 类型实现穷尽性检查。

## 正确示例

```typescript
import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/api-client";
import type { User, ApiResponse } from "@/types";

const API_TIMEOUT = 5000;

interface UserProfileProps {
    userId: string;
    onProfileLoaded?: (user: User) => void;
}

interface UserProfileState {
    user: User | null;
    isLoading: boolean;
    error: string | null;
}

function useUserProfile(userId: string): UserProfileState {
    const [state, setState] = useState<UserProfileState>({
        user: null,
        isLoading: true,
        error: null,
    });

    const loadProfile = useCallback(async () => {
        setState(prev => ({ ...prev, isLoading: true, error: null }));
        try {
            const response: ApiResponse<User> = await createClient()
                .get(`/users/${userId}`)
                .timeout(API_TIMEOUT);
            setState({ user: response.data, isLoading: false, error: null });
        } catch (err) {
            const message = err instanceof Error ? err.message : "Unknown error";
            setState({ user: null, isLoading: false, error: message });
        }
    }, [userId]);

    useEffect(() => {
        loadProfile();
    }, [loadProfile]);

    return state;
}

export default useUserProfile;
```

## 错误示例

```typescript
// 错误 1：使用 var
var items = [1, 2, 3];

// 错误 2：字符串拼接
const url = "https://api.example.com/users/" + userId + "/posts";

// 错误 3：使用 any
function process(data: any): any {
    return data.result;  // 没有类型安全
}
// 正确写法：
function process<T>(data: T): T extends { result: infer R } ? R : never {
    // ...
}

// 错误 4：函数缺少返回类型
async function fetchData() {
    const response = await fetch("/api/data");
    return response.json();
}
// 正确写法：
async function fetchData(): Promise<unknown> {
    const response = await fetch("/api/data");
    return response.json();
}

// 错误 5：未使用 await
async function saveUser(user: User) {
    db.save(user);  // 遗漏 await，可能未完成写入
    return true;
}

// 错误 6：使用 == 而非 ===
if (value == null) {  // == 会做类型转换
    // ...
}
// 正确写法：
if (value === null || value === undefined) {
    // ...
}
// 或使用 == null 同时匹配 null/undefined（Airbnb 允许此写法，但团队要求显式）

// 错误 7：直接修改 props / state（React）
function BadComponent(props: { items: string[] }) {
    props.items.push("new");  // 直接修改 props
    const [list, setList] = useState([1, 2, 3]);
    list.push(4);             // 直接修改 state
    return null;
}

// 错误 8：嵌套过多的三元表达式
const status = condition1 ? "a" : condition2 ? "b" : condition3 ? "c" : "d";
// 建议提取为函数或使用 if/else

// 错误 9：使用 || 作为默认值导致 0 / false 被吞掉
function Pagination({ page }: { page?: number }) {
    const currentPage = page || 1;  // 当 page = 0 时会被替换为 1
    return <div>Page {currentPage}</div>;
}
// 正确写法：
const currentPage = page ?? 1;
```

## 工具链配置

### ESLint 配置

```json
{
    "extends": [
        "airbnb",
        "airbnb-typescript",
        "airbnb/hooks",
        "plugin:@typescript-eslint/strict-type-checked",
        "prettier"
    ],
    "parserOptions": {
        "project": "./tsconfig.json"
    },
    "rules": {
        "import/prefer-default-export": "off",
        "react/react-in-jsx-scope": "off",
        "no-console": "warn",
        "@typescript-eslint/no-explicit-any": "error",
        "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }]
    }
}
```

### Prettier 配置

```json
{
    "semi": true,
    "singleQuote": true,
    "trailingComma": "all",
    "printWidth": 100,
    "tabWidth": 2,
    "arrowParens": "always",
    "endOfLine": "lf"
}
```

### tsconfig.json

```json
{
    "compilerOptions": {
        "target": "ES2022",
        "module": "ESNext",
        "moduleResolution": "bundler",
        "lib": ["ES2022", "DOM", "DOM.Iterable"],
        "strict": true,
        "noUncheckedIndexedAccess": true,
        "noImplicitReturns": true,
        "noFallthroughCasesInSwitch": true,
        "forceConsistentCasingInFileNames": true,
        "skipLibCheck": true,
        "jsx": "react-jsx",
        "baseUrl": ".",
        "paths": {
            "@/*": ["./src/*"]
        }
    },
    "include": ["src/**/*", "vite.config.ts"],
    "exclude": ["node_modules", "dist"]
}
```

## 参考来源

- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [TypeScript Handbook – Strict Mode](https://www.typescriptlang.org/tsconfig#strict)
- [ESLint Rules](https://eslint.org/docs/latest/rules/)
- [Prettier Options](https://prettier.io/docs/en/options.html)
- [TypeScript ESLint](https://typescript-eslint.io/)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
