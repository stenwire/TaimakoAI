describe('config', () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = { ...originalEnv };
    vi.resetModules();
  });

  it('returns localhost URLs when no environment is set', async () => {
    delete process.env.NEXT_PUBLIC_ENVIRONMENT;
    process.env.NODE_ENV = 'test';

    const config = await import('@/config');
    expect(config.BACKEND_URL).toBe('http://localhost:8000');
    expect(config.FRONTEND_URL).toBe('http://localhost:3000');
  });

  it('returns local URLs for local environment', async () => {
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'local';

    const config = await import('@/config');
    expect(config.BACKEND_URL).toBe('http://localhost:8000');
    expect(config.FRONTEND_URL).toBe('http://localhost:3000');
  });

  it('returns dev URLs for dev environment', async () => {
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'dev';

    const config = await import('@/config');
    expect(config.BACKEND_URL).toBe('https://api.dev.taimako.ai');
    expect(config.FRONTEND_URL).toBe('https://app.dev.taimako.ai');
  });

  it('returns staging URLs for staging environment', async () => {
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'staging';

    const config = await import('@/config');
    expect(config.BACKEND_URL).toBe('https://taimako.onrender.com');
    expect(config.FRONTEND_URL).toBe('https://taimakoai.onrender.com');
  });

  it('returns production URLs for production environment', async () => {
    process.env.NEXT_PUBLIC_ENVIRONMENT = 'production';

    const config = await import('@/config');
    expect(config.BACKEND_URL).toBe('https://api.taimako.dubem.xyz');
    expect(config.FRONTEND_URL).toBe('https://taimako.dubem.xyz');
  });

  it('treats NODE_ENV=production as production environment when NEXT_PUBLIC_ENVIRONMENT is unset', async () => {
    delete process.env.NEXT_PUBLIC_ENVIRONMENT;
    process.env.NODE_ENV = 'production';

    const config = await import('@/config');
    expect(config.BACKEND_URL).toBe('https://api.taimako.dubem.xyz');
    expect(config.FRONTEND_URL).toBe('https://taimako.dubem.xyz');
  });
});
