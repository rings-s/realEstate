<!-- src/routes/verify-email/+page.svelte -->
<script>
	import { goto } from '$app/navigation';
	import { verifyEmail } from '$lib/services/auth';

	let email = '';
	let code = '';
	let loading = false;
	let error = '';
	let success = false;

	async function handleSubmit() {
		loading = true;
		error = '';

		const result = await verifyEmail(email, code);

		loading = false;

		if (result.success) {
			success = true;
			setTimeout(() => goto('/'), 2000);
		} else {
			error = result.error || 'فشل التحقق. يرجى التأكد من صحة الرمز.';
		}
	}
</script>

<svelte:head>
	<title>التحقق من البريد الإلكتروني | منصة المزادات العقارية</title>
</svelte:head>

<div class="mx-auto max-w-md overflow-hidden rounded-lg bg-white shadow-md">
	<div class="p-6">
		<div class="mb-6 text-center">
			<h1 class="text-2xl font-bold text-slate-900">التحقق من البريد الإلكتروني</h1>
			<p class="mt-2 text-slate-600">أدخل الرمز المرسل إلى بريدك الإلكتروني للتحقق من حسابك</p>
		</div>

		{#if success}
			<div class="mb-6 rounded border-l-4 border-green-400 bg-green-50 p-4">
				<div class="flex">
					<div class="flex-shrink-0">
						<i class="fas fa-check-circle text-green-400"></i>
					</div>
					<div class="mr-3">
						<p class="text-sm text-green-700">
							تم التحقق من بريدك الإلكتروني بنجاح! جاري تحويلك...
						</p>
					</div>
				</div>
			</div>
		{:else if error}
			<div class="mb-6 rounded border-l-4 border-red-400 bg-red-50 p-4">
				<div class="flex">
					<div class="flex-shrink-0">
						<i class="fas fa-exclamation-circle text-red-400"></i>
					</div>
					<div class="mr-3">
						<p class="text-sm text-red-700">{error}</p>
					</div>
				</div>
			</div>
		{/if}

		<form on:submit|preventDefault={handleSubmit} class="space-y-4">
			<div>
				<label for="email" class="mb-1 block text-sm font-medium text-slate-700"
					>البريد الإلكتروني</label
				>
				<input
					type="email"
					id="email"
					bind:value={email}
					required
					class="input"
					placeholder="أدخل بريدك الإلكتروني"
					dir="ltr"
				/>
			</div>

			<div>
				<label for="code" class="mb-1 block text-sm font-medium text-slate-700">رمز التحقق</label>
				<input
					type="text"
					id="code"
					bind:value={code}
					required
					class="input"
					placeholder="أدخل رمز التحقق"
					dir="ltr"
				/>
			</div>

			<div>
				<button type="submit" class="btn-primary w-full" disabled={loading || success}>
					{#if loading}
						<i class="fas fa-spinner fa-spin ml-2"></i>
						جاري التحقق...
					{:else}
						تحقق من البريد الإلكتروني
					{/if}
				</button>
			</div>
		</form>

		<div class="mt-6 text-center">
			<p class="text-sm text-slate-600">
				لم تستلم رمز التحقق؟
				<button
					class="text-blue-600 hover:underline"
					on:click={() => {
						// Add resend verification code logic here
					}}
				>
					إعادة إرسال الرمز
				</button>
			</p>
		</div>
	</div>
</div>
