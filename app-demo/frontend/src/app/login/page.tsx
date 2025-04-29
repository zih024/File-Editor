import { LoginForm } from "@/components/login-form"
import { AuthProvider } from "@/contexts/auth-context"

export default function Page() {
  return (
    <AuthProvider>
      <div className="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-sm">
          <LoginForm />
        </div>
      </div>
    </AuthProvider>
  )
}
