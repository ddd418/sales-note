import {
  LayoutDashboard,
  Building2,
  Users,
  CheckSquare,
  List,
  Calendar,
  History,
  FileBarChart,
  GitBranch,
  Package,
  FileText,
  Mail,
  CreditCard,
  Bot,
  UserCircle,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";

const menuItems = [
  { title: "대시보드", url: "/", icon: LayoutDashboard },
  { title: "업체관리", url: "/companies", icon: Building2 },
  { title: "팔로우업", url: "/followup", icon: Users },
  { title: "TODOLIST", url: "/todos", icon: CheckSquare },
  { title: "일정 목록", url: "/schedules", icon: List },
  { title: "일정캘린더", url: "/calendar", icon: Calendar },
  { title: "히스토리", url: "/history", icon: History },
  { title: "고객 리포트", url: "/reports", icon: FileBarChart },
  { title: "펀넬관리", url: "/funnel", icon: GitBranch },
  { title: "제품관리", url: "/products", icon: Package },
  { title: "서류관리", url: "/documents", icon: FileText },
  { title: "메일함", url: "/mailbox", icon: Mail },
  { title: "명함관리", url: "/cards", icon: CreditCard },
  { title: "AI미팅준비", url: "/ai-meeting", icon: Bot },
  { title: "프로필관리", url: "/profile", icon: UserCircle },
];

export function AppSidebar() {
  const location = useLocation();
  const { state, toggleSidebar } = useSidebar();
  const isCollapsed = state === "collapsed";

  return (
    <Sidebar
      className="border-r border-sidebar-border bg-sidebar"
      collapsible="icon"
    >
      <SidebarHeader className="p-4 border-b border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">B</span>
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="font-semibold text-sidebar-foreground">B2B CRM</span>
              <span className="text-xs text-muted-foreground">영업 관리 시스템</span>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent className="px-2 py-4">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => {
                const isActive = location.pathname === item.url;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      tooltip={isCollapsed ? item.title : undefined}
                    >
                      <NavLink
                        to={item.url}
                        className={cn(
                          "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                          "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                          isActive && "bg-primary/10 text-primary border-l-2 border-primary"
                        )}
                      >
                        <item.icon className={cn(
                          "h-5 w-5 shrink-0",
                          isActive ? "text-primary" : "text-muted-foreground"
                        )} />
                        {!isCollapsed && (
                          <span className={cn(
                            "text-sm font-medium",
                            isActive ? "text-primary" : "text-sidebar-foreground"
                          )}>
                            {item.title}
                          </span>
                        )}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-2 border-t border-sidebar-border">
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleSidebar}
          className="w-full justify-center text-muted-foreground hover:text-foreground"
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 mr-2" />
              <span className="text-xs">접기</span>
            </>
          )}
        </Button>
      </SidebarFooter>
    </Sidebar>
  );
}
