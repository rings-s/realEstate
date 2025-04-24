// src/lib/services/properties.js
import { get } from 'svelte/store';
import { token } from './auth';

const API_URL = 'http://localhost:8000/api';

export async function fetchProperties(params = {}) {
	try {
		const accessToken = get(token);

		let queryParams = new URLSearchParams();
		for (const [key, value] of Object.entries(params)) {
			if (value) queryParams.append(key, value);
		}

		const headers = {
			'Content-Type': 'application/json'
		};

		if (accessToken) {
			headers['Authorization'] = `Bearer ${accessToken}`;
		}

		const res = await fetch(`${API_URL}/properties/?${queryParams.toString()}`, {
			headers
		});

		if (!res.ok) {
			const errorData = await res.json();
			throw new Error(errorData.error?.message || 'فشل في جلب العقارات');
		}

		const data = await res.json();
		return data.data;
	} catch (error) {
		console.error('Error fetching properties:', error);
		return { results: [], count: 0 };
	}
}

export async function fetchPropertyBySlug(slug) {
	try {
		const accessToken = get(token);

		const headers = {
			'Content-Type': 'application/json'
		};

		if (accessToken) {
			headers['Authorization'] = `Bearer ${accessToken}`;
		}

		const res = await fetch(`${API_URL}/properties/${slug}/`, {
			headers
		});

		if (!res.ok) {
			const errorData = await res.json();
			throw new Error(errorData.error?.message || 'فشل في جلب تفاصيل العقار');
		}

		const data = await res.json();
		return data.data;
	} catch (error) {
		console.error('Error fetching property:', error);
		return null;
	}
}

export async function createProperty(propertyData) {
	try {
		const accessToken = get(token);

		if (!accessToken) {
			throw new Error('يجب تسجيل الدخول لإضافة عقار');
		}

		const res = await fetch(`${API_URL}/properties/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${accessToken}`
			},
			body: JSON.stringify(propertyData)
		});

		if (!res.ok) {
			const errorData = await res.json();
			throw new Error(errorData.error?.message || 'فشل في إنشاء العقار');
		}

		const data = await res.json();
		return { success: true, data: data.data };
	} catch (error) {
		console.error('Error creating property:', error);
		return { success: false, error: error.message };
	}
}
