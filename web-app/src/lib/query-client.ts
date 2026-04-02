import { QueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { type AxiosError } from 'axios'

function getErrorMessage(error: unknown): string {
  const axiosError = error as AxiosError<{ detail?: string; message?: string }>
  return (
    axiosError.response?.data?.detail ??
    axiosError.response?.data?.message ??
    axiosError.message ??
    'An unexpected error occurred'
  )
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2,       // 2 minutes
      gcTime: 1000 * 60 * 10,          // 10 minutes
      retry: (failureCount, error) => {
        const status = (error as AxiosError)?.response?.status
        if (status && status >= 400 && status < 500) return false
        return failureCount < 2
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      onError: (error) => {
        toast.error(getErrorMessage(error))
      },
    },
  },
})
