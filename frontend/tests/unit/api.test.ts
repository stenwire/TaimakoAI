import { setTokens, getAccessToken, getRefreshToken, clearTokens } from '@/lib/api';

// Mock axios before importing api module (which creates an axios instance at import time)
vi.mock('axios', async () => {
  const mockAxiosInstance = {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: { headers: { common: {} } },
  };

  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
    },
    AxiosError: class AxiosError extends Error {},
  };
});

describe('token management', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('setTokens stores access_token in localStorage', () => {
    setTokens({ access_token: 'abc', refresh_token: 'def', token_type: 'bearer' });
    expect(localStorage.getItem('access_token')).toBe('abc');
  });

  it('setTokens stores refresh_token in localStorage', () => {
    setTokens({ access_token: 'abc', refresh_token: 'def', token_type: 'bearer' });
    expect(localStorage.getItem('refresh_token')).toBe('def');
  });

  it('getAccessToken returns the stored access token', () => {
    localStorage.setItem('access_token', 'my-token');
    expect(getAccessToken()).toBe('my-token');
  });

  it('getAccessToken returns null when no token is stored', () => {
    expect(getAccessToken()).toBeNull();
  });

  it('getRefreshToken returns the stored refresh token', () => {
    localStorage.setItem('refresh_token', 'my-refresh');
    expect(getRefreshToken()).toBe('my-refresh');
  });

  it('getRefreshToken returns null when no token is stored', () => {
    expect(getRefreshToken()).toBeNull();
  });

  it('clearTokens removes access_token from localStorage', () => {
    localStorage.setItem('access_token', 'abc');
    clearTokens();
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('clearTokens removes refresh_token from localStorage', () => {
    localStorage.setItem('refresh_token', 'def');
    clearTokens();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });
});

describe('API functions', () => {
  let mockAxiosInstance: {
    post: ReturnType<typeof vi.fn>;
    get: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    localStorage.clear();
    const axios = await import('axios');
    // Get the mock instance that was returned by axios.create()
    mockAxiosInstance = (axios.default.create as ReturnType<typeof vi.fn>).mock.results[0]?.value;
  });

  it('signup calls api.post with correct endpoint and data', async () => {
    const { signup } = await import('@/lib/api');
    const mockResponse = {
      data: {
        status: 'success',
        message: 'ok',
        data: { access_token: 'at', refresh_token: 'rt', token_type: 'bearer' },
      },
    };
    mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

    await signup({ email: 'test@example.com', password: 'pass123', name: 'Test' });

    expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/signup', {
      email: 'test@example.com',
      password: 'pass123',
      name: 'Test',
    });
  });

  it('signup stores tokens on success', async () => {
    const { signup } = await import('@/lib/api');
    const mockResponse = {
      data: {
        status: 'success',
        message: 'ok',
        data: { access_token: 'signup-at', refresh_token: 'signup-rt', token_type: 'bearer' },
      },
    };
    mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

    await signup({ email: 'test@example.com', password: 'pass123', name: 'Test' });

    expect(localStorage.getItem('access_token')).toBe('signup-at');
    expect(localStorage.getItem('refresh_token')).toBe('signup-rt');
  });

  it('login calls api.post with correct endpoint and data', async () => {
    const { login } = await import('@/lib/api');
    const mockResponse = {
      data: {
        status: 'success',
        message: 'ok',
        data: { access_token: 'at', refresh_token: 'rt', token_type: 'bearer' },
      },
    };
    mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

    await login({ email: 'test@example.com', password: 'pass123' });

    expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/login', {
      email: 'test@example.com',
      password: 'pass123',
    });
  });

  it('login stores tokens on success', async () => {
    const { login } = await import('@/lib/api');
    const mockResponse = {
      data: {
        status: 'success',
        message: 'ok',
        data: { access_token: 'login-at', refresh_token: 'login-rt', token_type: 'bearer' },
      },
    };
    mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

    await login({ email: 'test@example.com', password: 'pass123' });

    expect(localStorage.getItem('access_token')).toBe('login-at');
    expect(localStorage.getItem('refresh_token')).toBe('login-rt');
  });

  it('logout clears tokens from localStorage', async () => {
    const { logout } = await import('@/lib/api');
    localStorage.setItem('access_token', 'old-at');
    localStorage.setItem('refresh_token', 'old-rt');

    logout();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });
});
