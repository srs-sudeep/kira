export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ApiError {
  detail: string
  code?: string
  field?: string
}

export interface ApiValidationError {
  detail: Array<{
    loc: Array<string | number>
    msg: string
    type: string
  }>
}

export interface SuccessResponse {
  message: string
}

export interface ListParams {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
}
