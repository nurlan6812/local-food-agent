import { toast } from "sonner"

export function useToast() {
  return {
    toast: ({ title, description, variant }: {
      title?: string;
      description?: string;
      variant?: 'default' | 'destructive'
    }) => {
      if (variant === 'destructive') {
        toast.error(title, { description })
      } else {
        toast(title, { description })
      }
    },
  }
}
