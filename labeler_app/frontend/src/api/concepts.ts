import { apiClient } from './client'
import type { ConceptPromptResponse } from '../types'

export interface TextPromptRequest {
  text: string
  threshold?: number
  create_annotations?: boolean
  label_class_id?: number | null
  author?: string | null
}

export interface ExemplarPromptRequest {
  crop: { x: number; y: number; w: number; h: number }
  type: 'positive' | 'negative'
  search_dataset?: boolean
  threshold?: number
  create_annotations?: boolean
  label_class_id?: number | null
  author?: string | null
}

export const promptImageWithText = async (
  projectId: number,
  imageId: number,
  request: TextPromptRequest,
): Promise<ConceptPromptResponse> => {
  const { data } = await apiClient.post<ConceptPromptResponse>(
    `/concepts/projects/${projectId}/images/${imageId}/prompt`,
    request,
  )
  return data
}

export const promptImageWithExemplar = async (
  projectId: number,
  imageId: number,
  request: ExemplarPromptRequest,
): Promise<ConceptPromptResponse> => {
  const { data } = await apiClient.post<ConceptPromptResponse>(
    `/concepts/projects/${projectId}/images/${imageId}/exemplar`,
    request,
  )
  return data
}

