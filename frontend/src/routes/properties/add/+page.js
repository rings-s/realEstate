// src/routes/properties/add/+page.js

import { redirect } from '@sveltejs/kit';
import { get } from 'svelte/store';
import { isAuthenticated, isVerified } from '$lib/stores/auth';

export const load = async ({ url, fetch, depends }) => {
  depends('auth:status');

  const authenticated = get(isAuthenticated);
  const verified = get(isVerified);

  if (!authenticated) {
    throw redirect(302, `/login?redirect=${encodeURIComponent(url.pathname)}`);
  }

  if (!verified) {
    throw redirect(302, '/verify-email');
  }

  return {
    authenticated,
    verified
  };
};