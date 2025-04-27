<script>
	import { goto } from '$app/navigation';
	import { login } from '$lib/stores/auth';
	import { addToast } from '$lib/stores/ui';
  
	export let redirectTo = '/';
  
	let email = '';
	let password = '';
	let rememberMe = false;
	let loading = false;
	let error = '';
  
	async function handleSubmit() {
	  if (!email || !password) {
		error = 'Please enter both email and password';
		return;
	  }
  
	  loading = true;
	  error = '';
  
	  try {
		const result = await login(email, password);
		
		if (result.success) {
		  addToast('تم تسجيل الدخول بنجاح', 'success');
		  goto(redirectTo);
		} else {
		  error = result.error || 'خطأ في تسجيل الدخول. يرجى التحقق من بياناتك.';
		}
	  } catch (err) {
		console.error('Login error:', err);
		error = 'حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.';
	  } finally {
		loading = false;
	  }
	}
  </script>
  
  <form on:submit|preventDefault={handleSubmit} class="space-y-4">
	{#if error}
	  <div class="rounded-lg border-l-4 border-red-500 bg-red-50 p-4 text-red-700">
		<p class="text-sm">{error}</p>
	  </div>
	{/if}
  
	<div>
	  <label for="email" class="mb-1 block text-sm font-medium text-slate-700">
		البريد الإلكتروني
	  </label>
	  <input
		type="email"
		id="email"
		bind:value={email}
		required
		class="input"
		placeholder="أدخل بريدك الإلكتروني"
		disabled={loading}
	  />
	</div>
  
	<div>
	  <label for="password" class="mb-1 block text-sm font-medium text-slate-700">
		كلمة المرور
	  </label>
	  <input
		type="password"
		id="password"
		bind:value={password}
		required
		class="input"
		placeholder="أدخل كلمة المرور"
		disabled={loading}
	  />
	</div>
  
	<div class="flex items-center justify-between">
	  <div class="flex items-center">
		<input
		  type="checkbox"
		  id="remember"
		  bind:checked={rememberMe}
		  class="h-4 w-4 rounded border-gray-300 text-blue-600"
		  disabled={loading}
		/>
		<label for="remember" class="mr-2 text-sm text-slate-700">
		  تذكرني
		</label>
	  </div>
  
	  <a href="/reset-password/request" class="text-sm text-blue-600 hover:underline">
		نسيت كلمة المرور؟
	  </a>
	</div>
  
	<button
	  type="submit"
	  class="btn-primary w-full"
	  disabled={loading}
	>
	  {#if loading}
		<i class="fas fa-spinner fa-spin ml-2"></i>
		جاري تسجيل الدخول...
	  {:else}
		تسجيل الدخول
	  {/if}
	</button>
  </form>
  
  <div class="mt-6 text-center">
	<p class="text-sm text-slate-600">
	  ليس لديك حساب؟
	  <a href="/register" class="text-blue-600 hover:underline">
		إنشاء حساب جديد
	  </a>
	</p>
  </div>