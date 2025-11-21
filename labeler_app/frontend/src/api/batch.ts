import { apiClient } from './client'

export interface BatchLabelRequest {
  concept_text: string
  threshold?: number
  skip_empty?: boolean
  create_annotations?: boolean
  label_class_id?: number | null
  author?: string | null
}

export interface BatchJobResponse {
  job_id: string
  dataset_id: number
  concept_text: string
  status: string
  total_images: number
  message: string
}

export interface BatchJobStatus {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_images: number
  processed: number
  succeeded: number
  failed: number
  skipped: number
  progress: number
  message?: string | null
  errors?: string[] | null
}

export const createBatchJob = async (
  projectId: number,
  datasetId: number,
  request: BatchLabelRequest,
): Promise<BatchJobResponse> => {
  const { data } = await apiClient.post<BatchJobResponse>(
    `/batch/projects/${projectId}/datasets/${datasetId}/label`,
    request,
  )
  return data
}

export const getBatchJobStatus = async (jobId: string): Promise<BatchJobStatus> => {
  const { data } = await apiClient.get<BatchJobStatus>(`/batch/jobs/${jobId}`)
  return data
}

export const listBatchJobs = async (limit = 50): Promise<BatchJobStatus[]> => {
  const { data } = await apiClient.get<BatchJobStatus[]>('/batch/jobs', { params: { limit } })
  return data
}

