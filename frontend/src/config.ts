export type Environment = 'local' | 'dev' | 'staging' | 'production';

export const ENVIRONMENT = (process.env.NEXT_PUBLIC_ENVIRONMENT as Environment) ||
  (process.env.NODE_ENV === 'production' ? 'production' : 'local');

const getBackendUrl = (): string => {
  switch (ENVIRONMENT) {
    case 'production':
      return process.env.NEXT_PUBLIC_BACKEND_URL_PROD || 'https://api.taimako.dubem.xyz';
    case 'staging':
      return process.env.NEXT_PUBLIC_BACKEND_URL_STAGING || 'https://api.staging.taimako.ai';
    case 'dev':
      return process.env.NEXT_PUBLIC_BACKEND_URL_DEV || 'https://api.dev.taimako.ai';
    case 'local':
    default:
      return process.env.NEXT_PUBLIC_BACKEND_URL_LOCAL || 'http://localhost:8000';
  }
};

const getFrontendUrl = (): string => {
  switch (ENVIRONMENT) {
    case 'production':
      return process.env.NEXT_PUBLIC_FRONTEND_URL_PROD || 'https://taimako.dubem.xyz';
    case 'staging':
      return process.env.NEXT_PUBLIC_FRONTEND_URL_STAGING || 'https://app.staging.taimako.ai';
    case 'dev':
      return process.env.NEXT_PUBLIC_FRONTEND_URL_DEV || 'https://app.dev.taimako.ai';
    case 'local':
    default:
      return process.env.NEXT_PUBLIC_FRONTEND_URL_LOCAL || 'http://localhost:3000';
  }
};

export const BACKEND_URL = getBackendUrl();
export const FRONTEND_URL = getFrontendUrl();
