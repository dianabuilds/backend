# Code Style

Проект использует ESLint и Prettier для обеспечения единообразия кода.

## Naming

- Переменные и функции: `camelCase`.
- Компоненты React и классы: `PascalCase`.
- Константы: `SCREAMING_SNAKE_CASE`.

## ESLint before/after

До:
```ts
const foo = 1
if(foo==2){
 console.log('bad')
}
```

После:
```ts
const foo = 1;

if (foo === 2) {
  console.log('bad');
}
```

## Prettier before/after

До:
```ts
const user={id:1,name:"Tom"}
```

После:
```ts
const user = { id: 1, name: 'Tom' };
```
