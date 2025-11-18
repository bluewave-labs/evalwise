import PlaygroundClient from './playground-client'
import ProtectedRoute from '@/components/protected-route'

export default function PlaygroundPage() {
  return (
    <ProtectedRoute>
      <PlaygroundClient />
    </ProtectedRoute>
  )
}
