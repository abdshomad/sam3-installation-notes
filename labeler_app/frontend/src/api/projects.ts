import { apiClient } from './client'
import type { Annotation, Dataset, ImageAsset, LabelClass, Project } from '../types'

export const fetchProjects = async (): Promise<Project[]> => {
  const { data } = await apiClient.get<Project[]>('/projects')
  return data
}

export const createProject = async (payload: { name: string; description?: string }) => {
  const { data } = await apiClient.post<Project>('/projects', payload)
  return data
}

export const fetchProject = async (projectId: number) => {
  const { data } = await apiClient.get<Project>(`/projects/${projectId}`)
  return data
}

export const fetchLabelClasses = async (projectId: number) => {
  const { data } = await apiClient.get<LabelClass[]>(`/projects/${projectId}/classes`)
  return data
}

export const createLabelClass = async (
  projectId: number,
  payload: { name: string; color: string; hotkey?: string },
) => {
  const { data } = await apiClient.post<LabelClass>(`/projects/${projectId}/classes`, payload)
  return data
}

export const fetchDatasets = async (projectId?: number) => {
  const { data } = await apiClient.get<Dataset[]>('/datasets', { params: { project_id: projectId } })
  return data
}

export const createDataset = async (projectId: number, payload: { name: string; description?: string }) => {
  const { data } = await apiClient.post<Dataset>('/datasets', payload, {
    params: { project_id: projectId },
  })
  return data
}

export const fetchDataset = async (datasetId: number) => {
  const { data } = await apiClient.get<Dataset>(`/datasets/${datasetId}`)
  return data
}

export const uploadImages = async (datasetId: number, files: FileList) => {
  const formData = new FormData()
  Array.from(files).forEach((file) => formData.append('files', file))
  const { data } = await apiClient.post<ImageAsset[]>('/images/upload', formData, {
    params: { dataset_id: datasetId },
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const fetchImages = async (datasetId: number) => {
  const { data } = await apiClient.get<ImageAsset[]>('/images', { params: { dataset_id: datasetId, limit: 500 } })
  return data
}

export const fetchAnnotations = async (imageId: number) => {
  const { data } = await apiClient.get<Annotation[]>('/annotations', { params: { image_id: imageId } })
  return data
}

export const createAnnotation = async (payload: {
  image_id: number
  label_class_id: number
  annotation_type: string
  geometry: Record<string, unknown>
}) => {
  const { data } = await apiClient.post<Annotation>('/annotations', payload)
  return data
}

