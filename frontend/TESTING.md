# Testing Guide

Standards and conventions for writing tests in the TaimakoAI frontend.

## Quick Start

```bash
# Run full suite
make test-fe           # via Makefile
npm test               # directly
npx vitest run         # equivalent

# Watch mode (re-runs on file change)
npm run test:watch

# Run a single file
npx vitest run tests/unit/utils.test.ts

# Run tests matching a name
npx vitest run -t "renders children"
```

## Stack

| Tool                      | Purpose                              |
| ------------------------- | ------------------------------------ |
| **Vitest**                | Test runner and assertion library     |
| **jsdom**                 | Browser environment simulation       |
| **@testing-library/react**| Component rendering and queries      |
| **@testing-library/user-event** | User interaction simulation    |
| **@testing-library/jest-dom** | DOM assertion matchers (`.toBeInTheDocument()`, etc.) |

## Directory Structure

```
tests/
  setup.tsx               # Global setup: jest-dom matchers, framer-motion mock, next/navigation mock
  unit/                   # Pure logic tests — no components
    utils.test.ts         # cn() utility
    config.test.ts        # Environment URL selection
    api.test.ts           # Token management, API functions
    toast-context.test.tsx # ToastProvider context + hook
  components/             # UI component tests
    Button.test.tsx
    Input.test.tsx
    Card.test.tsx
    Modal.test.tsx
    UsageRates.test.tsx
```

### Where does my test go?

| You are testing...                        | Put it in...         |
| ----------------------------------------- | -------------------- |
| A utility function (no JSX)               | `tests/unit/`        |
| A React context or hook                   | `tests/unit/`        |
| A UI component (`components/ui/`)         | `tests/components/`  |
| A dashboard component                     | `tests/components/`  |

## Writing a Test

### Naming

Follow `test_<what>_<scenario>_<expected>`:

```tsx
it("renders children text", () => { ... });
it("shows loading spinner when loading is true", () => { ... });
it("calls onClick when button is clicked", () => { ... });
```

Group related tests with `describe`:

```tsx
describe("Button", () => {
  describe("variants", () => {
    it("renders primary variant", () => { ... });
    it("renders ghost variant", () => { ... });
  });

  describe("loading state", () => {
    it("shows spinner", () => { ... });
    it("disables button", () => { ... });
  });
});
```

### Component Tests

Use `render` and `screen` from Testing Library:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Button from "@/components/ui/Button";

describe("Button", () => {
  it("fires onClick handler", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();

    render(<Button onClick={handleClick}>Click me</Button>);
    await user.click(screen.getByRole("button"));

    expect(handleClick).toHaveBeenCalledOnce();
  });
});
```

### Context / Hook Tests

Use `renderHook` with a wrapper:

```tsx
import { renderHook, act } from "@testing-library/react";
import { ToastProvider, useToast } from "@/contexts/ToastContext";

it("adds a success toast", () => {
  const { result } = renderHook(() => useToast(), {
    wrapper: ToastProvider,
  });

  act(() => {
    result.current.success("Done!");
  });

  // Assert toast rendered in the DOM
});
```

### Mocking

#### API calls (axios)

```tsx
import { vi } from "vitest";
import axios from "axios";

vi.mock("axios", () => {
  const instance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: { headers: { common: {} } },
  };
  return {
    default: { create: vi.fn(() => instance), ...instance },
  };
});
```

#### framer-motion

Already mocked globally in `tests/setup.tsx`. `motion.div` renders as a plain `<div>`.

#### next/navigation

Already mocked globally. `useRouter()` returns `{ push: vi.fn(), replace: vi.fn(), ... }`.

#### localStorage

jsdom provides `localStorage` by default. Reset between tests with:

```tsx
beforeEach(() => {
  localStorage.clear();
});
```

### What to Test

**Do test:**
- Component renders correct content based on props
- User interactions trigger callbacks
- Conditional rendering (loading, error, empty states)
- Context providers expose correct values
- Utility functions return correct output
- Form elements forward refs and attributes

**Don't test:**
- Exact CSS class names or styles (they use CSS variables)
- Third-party library behavior (framer-motion animations, axios internals)
- Next.js routing or SSR behavior
- Pixel-perfect layout

## When to Write Tests

### Always write tests when you:

- **Add a new UI component** — Add to `tests/components/`.
- **Add a new context or hook** — Add to `tests/unit/`.
- **Add a new utility function** — Add to `tests/unit/`.
- **Fix a bug** — Write a regression test that reproduces the bug.
- **Change component props or behavior** — Update existing tests.

### You can skip tests for:

- Page files that just compose existing components with no logic.
- Style-only changes (colors, spacing, fonts).
- Static content changes (text, copy).

### PR checklist

- [ ] All tests pass: `npm test`
- [ ] Lint passes: `npm run lint`
- [ ] New components have corresponding tests
- [ ] No hardcoded API URLs or secrets in test files
- [ ] Mocks are scoped properly (per-test or per-file, not leaking)

## Tips

1. **Query by role, not test-id.** Prefer `screen.getByRole("button")` over `screen.getByTestId("btn")`. This tests accessibility too.

2. **Use `userEvent` over `fireEvent`.** `userEvent.setup()` simulates real user behavior (focus, keyboard, pointer events). `fireEvent` dispatches raw DOM events.

3. **Don't test implementation details.** Test what the user sees and does, not internal state or method calls.

4. **Keep tests independent.** Each test should work in isolation. Use `beforeEach` for shared setup.

5. **Mock at the boundary.** Mock `api.post`, not `axios.post`. Mock the service, not the transport.

6. **Fake timers for timeouts.** Use `vi.useFakeTimers()` and `vi.advanceTimersByTime()` for testing auto-dismiss, debounce, etc. Always call `vi.useRealTimers()` in cleanup.
