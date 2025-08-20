import { describe, it, expect, vi, beforeEach } from 'vitest';

// Provide a complete mock inside the factory (no external refs) so hoisting won't break things.
// The factory returns an axios-like module whose .create returns a mock client object.
vi.mock('axios', () => {
  const mockApiClient = {
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  };

  return {
    default: {
      create: vi.fn(() => mockApiClient)
    }
  };
});

import axios from 'axios';
import ApiService from '../../src/services/api.service';

// Grab the mock client that was returned by axios.create during module init
const mockApiClient = (axios as any).create.mock.results[0].value;

describe('ApiService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should GET data', async () => {
    mockApiClient.get.mockResolvedValue({ data: { foo: 1 } });
    const res = await ApiService.get('/test');
    expect(res.success).toBe(true);
    expect(res.data).toEqual({ foo: 1 });
  });

  it('should POST data', async () => {
    mockApiClient.post.mockResolvedValue({ data: { bar: 2 } });
    const res = await ApiService.post('/test', { a: 1 });
    expect(res.success).toBe(true);
    expect(res.data).toEqual({ bar: 2 });
  });

  it('should PUT data', async () => {
    mockApiClient.put.mockResolvedValue({ data: { baz: 3 } });
    const res = await ApiService.put('/test', { b: 2 });
    expect(res.success).toBe(true);
    expect(res.data).toEqual({ baz: 3 });
  });

  it('should DELETE data', async () => {
    mockApiClient.delete.mockResolvedValue({ data: { ok: true } });
    const res = await ApiService.delete('/test');
    expect(res.success).toBe(true);
    expect(res.data).toEqual({ ok: true });
  });

  it('should handle error response', async () => {
    mockApiClient.get.mockRejectedValue({ message: 'fail', type: 'ApiError' });
    const res = await ApiService.get('/fail');
    expect(res.success).toBe(false);
    expect(res.error).toBeDefined();
  });

  it('should upload file', async () => {
    mockApiClient.post.mockResolvedValue({ data: { uploaded: true } });
    const file = new File(['a'], 'a.csv', { type: 'text/csv' });
    const res = await ApiService.uploadFile('/upload', file);
    expect(res.success).toBe(true);
    expect(res.data).toEqual({ uploaded: true });
  });
});