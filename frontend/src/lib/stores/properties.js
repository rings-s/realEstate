// src/lib/stores/properties.js
import { writable, derived } from 'svelte/store';
import api from '$lib/services/api';
import { addToast } from '$lib/stores/ui';

export const properties = writable([]);
export const currentProperty = writable(null);
export const propertiesCount = writable(0);
export const loadingProperties = writable(false);
export const propertyError = writable(null);

export const hasProperties = derived(
  [properties, propertiesCount],
  ([$properties, $propertiesCount]) => $properties.length > 0 || $propertiesCount > 0
);

export async function fetchProperties(params = {}) {
  loadingProperties.set(true);
  propertyError.set(null);

  try {
    console.log('Loading properties with params:', params);
    
    // Clean up params - remove empty values
    const cleanParams = {};
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        cleanParams[key] = value;
      }
    });
    
    const response = await api.get('/properties/', cleanParams);
    console.log('API response:', response);

    if (response.status === 'success') {
      const results = response.data.results || [];
      const count = response.data.count || 0;

      properties.set(results);
      propertiesCount.set(count);

      return { results, count };
    } else {
      console.error('API Error:', response.error);
      throw new Error(response.error || 'Failed to fetch properties');
    }
  } catch (error) {
    console.error('Error fetching properties:', error);
    propertyError.set(error.message);
    properties.set([]);
    propertiesCount.set(0);
    return { results: [], count: 0 };
  } finally {
    loadingProperties.set(false);
  }
}

export async function fetchPropertyBySlug(slug) {
  if (!slug) {
    propertyError.set('Invalid property ID');
    return null;
  }

  loadingProperties.set(true);
  propertyError.set(null);

  try {
    const response = await api.get(`/properties/${slug}/`);

    if (response.status === 'success') {
      currentProperty.set(response.data);
      return response.data;
    } else {
      throw new Error(response.error || 'Failed to fetch property');
    }
  } catch (error) {
    console.error('Error fetching property:', error);
    propertyError.set(error.message);
    currentProperty.set(null);
    return null;
  } finally {
    loadingProperties.set(false);
  }
}

// In properties.js
export async function createProperty(propertyData) {
	loadingProperties.set(true);
	propertyError.set(null);
	
	try {
	  console.log('Creating property with data:', propertyData);
	  
	  // Create FormData
	  const formData = new FormData();
  
	  // List of fields that need JSON stringification
	  const jsonFields = ['location', 'features', 'amenities', 'rooms', 
						   'specifications', 'pricing_details', 'highQualityStreets'];
	  
	  // Process each field
	  Object.entries(propertyData).forEach(([key, value]) => {
		if (value === null || value === undefined) return;
		
		// Special handling for JSON fields
		if (jsonFields.includes(key)) {
		  // Always stringify these fields properly
		  try {
			const jsonValue = JSON.stringify(value);
			formData.append(key, jsonValue);
			console.log(`Added JSON field ${key}:`, jsonValue);
		  } catch (e) {
			console.error(`Failed to stringify ${key}:`, e);
			// Use appropriate default
			const defaultValue = ['features', 'amenities', 'rooms', 'highQualityStreets'].includes(key) 
			  ? '[]' : '{}';
			formData.append(key, defaultValue);
		  }
		}
		// Handle media files
		else if (key === 'media' && Array.isArray(value)) {
		  value.forEach(file => {
			if (file instanceof File) {
			  formData.append('media', file);
			  console.log(`Added media file: ${file.name}`);
			}
		  });
		}
		// Regular fields
		else {
		  formData.append(key, value);
		  console.log(`Added field ${key}: ${value}`);
		}
	  });
  
	  // API request
	  const response = await api.post('/properties/', formData);
	  console.log('Property creation response:', response);
  
	  if (response.status === 'success' && response.data) {
		return { success: true, data: response.data };
	  } else {
		throw new Error(response.error || 'Failed to create property');
	  }
	} catch (error) {
	  console.error('Property creation error details:', error);
	  propertyError.set(error.message);
	  return { success: false, error: error.message };
	} finally {
	  loadingProperties.set(false);
	}
}


export async function updateProperty(slug, propertyData) {
  if (!slug) {
    return { success: false, error: 'Invalid property ID' };
  }

  loadingProperties.set(true);
  propertyError.set(null);

  try {
    // Create a FormData object
    const formData = new FormData();

    // Add all property data to FormData
    for (const [key, value] of Object.entries(propertyData)) {
      if (value !== null && value !== undefined) {
        if (key !== 'media' && typeof value === 'object') {
          formData.append(key, JSON.stringify(value));
        } else if (key === 'media' && Array.isArray(value)) {
          value.forEach((file) => {
            if (file instanceof File) {
              formData.append('media', file);
            }
          });
        } else {
          formData.append(key, value);
        }
      }
    }

    const response = await api.patch(`/properties/${slug}/`, formData);

    if (response.status === 'success') {
      // Update current property if it matches
      currentProperty.update((prop) => {
        if (prop && prop.slug === slug) {
          return response.data;
        }
        return prop;
      });

      // Update in properties list if present
      properties.update(props => 
        props.map(p => p.slug === slug ? response.data : p)
      );

      addToast('تم تحديث العقار بنجاح', 'success');
      return { success: true, data: response.data };
    } else {
      throw new Error(response.error || 'Failed to update property');
    }
  } catch (error) {
    console.error('Error updating property:', error);
    propertyError.set(error.message);
    addToast(error.message || 'فشل في تحديث العقار', 'error');
    return { success: false, error: error.message };
  } finally {
    loadingProperties.set(false);
  }
}

export async function deleteProperty(slug) {
  if (!slug) {
    return { success: false, error: 'Invalid property ID' };
  }

  loadingProperties.set(true);
  propertyError.set(null);

  try {
    const response = await api.delete(`/properties/${slug}/`);

    if (response.status === 'success') {
      // Remove from properties list
      properties.update(props => props.filter(p => p.slug !== slug));
      
      // Clear current property if it's the deleted one
      currentProperty.update(prop => {
        if (prop && prop.slug === slug) {
          return null;
        }
        return prop;
      });

      addToast('تم حذف العقار بنجاح', 'success');
      return { success: true };
    } else {
      throw new Error(response.error || 'Failed to delete property');
    }
  } catch (error) {
    console.error('Error deleting property:', error);
    propertyError.set(error.message);
    addToast(error.message || 'فشل في حذف العقار', 'error');
    return { success: false, error: error.message };
  } finally {
    loadingProperties.set(false);
  }
}

// Function to toggle property favorite status
export async function togglePropertyFavorite(propertyId) {
  try {
    const response = await api.post(`/properties/${propertyId}/toggle-favorite/`);
    
    if (response.status === 'success') {
      // Update property in store
      properties.update(props => 
        props.map(p => p.id === propertyId ? 
          {...p, is_favorite: !p.is_favorite} : p)
      );
      
      // Update current property if it matches
      currentProperty.update(prop => {
        if (prop && prop.id === propertyId) {
          return {...prop, is_favorite: !prop.is_favorite};
        }
        return prop;
      });
      
      return { success: true, isFavorite: response.data?.is_favorite };
    } else {
      throw new Error(response.error || 'Failed to update favorite status');
    }
  } catch (error) {
    console.error('Error toggling favorite:', error);
    return { success: false, error: error.message };
  }
}

// Export a default object with all functions
export default {
  fetchProperties,
  fetchPropertyBySlug,
  createProperty,
  updateProperty,
  deleteProperty,
  togglePropertyFavorite,
  properties,
  currentProperty,
  propertiesCount,
  loadingProperties,
  propertyError,
  hasProperties
};