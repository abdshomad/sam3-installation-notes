export interface Project {
  id: number
  name: string
  description?: string | null
  slug: string
  created_at: string
  updated_at: string
}

export interface LabelClass {
  id: number
  name: string
  color: string
  hotkey?: string | null
  order_index: number
  project_id: number
}

export interface Dataset {
  id: number
  name: string
  description?: string | null
  slug: string
  project_id: number
  status: string
  created_at: string
  updated_at: string
}

export interface ImageAsset {
  id: number
  dataset_id: number
  original_filename: string
  width?: number | null
  height?: number | null
  file_path: string
  status: string
  created_at: string
  updated_at: string
}

export interface Annotation {
  id: number
  image_id: number
  label_class_id: number
  annotation_type: string
  geometry: Record<string, any>
  attributes?: Record<string, any> | null
  author?: string | null
  created_at: string
  updated_at: string
}

