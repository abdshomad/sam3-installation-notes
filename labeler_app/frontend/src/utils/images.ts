import { API_BASE_URL } from '../config'

export const buildImageUrl = (imageId: number) => `${API_BASE_URL}/images/${imageId}/content`

