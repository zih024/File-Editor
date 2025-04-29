import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AuthProvider } from "@/contexts/auth-context";

export default function Layout({children}: {children: React.ReactNode}) {
    return (
        <AuthProvider>
            <SidebarProvider>
                <AppSidebar />
                <SidebarTrigger />
                <main className="flex-1">
                    {children}
                </main>
            </SidebarProvider>
        </AuthProvider>
    )
}