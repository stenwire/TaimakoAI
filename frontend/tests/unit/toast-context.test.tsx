import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderHook } from '@testing-library/react';
import { ToastProvider, useToast } from '@/contexts/ToastContext';

describe('useToast', () => {
  it('throws when used outside ToastProvider', () => {
    // Suppress console.error for expected error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => renderHook(() => useToast())).toThrow(
      'useToast must be used within a ToastProvider'
    );
    spy.mockRestore();
  });

  it('does not throw when used inside ToastProvider', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <ToastProvider>{children}</ToastProvider>
    );
    const { result } = renderHook(() => useToast(), { wrapper });
    expect(result.current).toBeDefined();
  });
});

describe('ToastProvider rendering', () => {
  function TestComponent({ type, message }: { type: 'success' | 'error'; message: string }) {
    const toast = useToast();
    return (
      <button onClick={() => toast[type](message)}>
        show-{type}
      </button>
    );
  }

  it('renders a success toast with the correct message', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TestComponent type="success" message="Operation succeeded" />
      </ToastProvider>
    );

    await user.click(screen.getByText('show-success'));

    expect(screen.getByText('Operation succeeded')).toBeInTheDocument();
  });

  it('renders an error toast with the correct message', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <TestComponent type="error" message="Something went wrong" />
      </ToastProvider>
    );

    await user.click(screen.getByText('show-error'));

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('auto-removes toast after timeout', () => {
    vi.useFakeTimers();

    render(
      <ToastProvider>
        <TestComponent type="success" message="Temporary toast" />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('show-success'));
    expect(screen.getByText('Temporary toast')).toBeInTheDocument();

    // Advance past the 3 second auto-remove timeout
    act(() => {
      vi.advanceTimersByTime(3500);
    });

    expect(screen.queryByText('Temporary toast')).not.toBeInTheDocument();

    vi.useRealTimers();
  });

  it('dismiss button removes the toast', () => {
    render(
      <ToastProvider>
        <TestComponent type="success" message="Dismissable toast" />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('show-success'));
    expect(screen.getByText('Dismissable toast')).toBeInTheDocument();

    // Find the dismiss (X) button - it is the button that is not our trigger
    const allButtons = screen.getAllByRole('button');
    const xButton = allButtons.find((btn) => btn.textContent !== 'show-success');
    expect(xButton).toBeDefined();

    fireEvent.click(xButton!);

    expect(screen.queryByText('Dismissable toast')).not.toBeInTheDocument();
  });
});
