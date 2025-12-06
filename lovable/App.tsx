import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Companies from "./pages/Companies";
import Followup from "./pages/Followup";
import FollowupDetail from "./pages/FollowupDetail";
import Todos from "./pages/Todos";
import Schedules from "./pages/Schedules";
import CalendarPage from "./pages/CalendarPage";
import History from "./pages/History";
import Reports from "./pages/Reports";
import Funnel from "./pages/Funnel";
import Products from "./pages/Products";
import Documents from "./pages/Documents";
import Mailbox from "./pages/Mailbox";
import BusinessCards from "./pages/BusinessCards";
import AIMeeting from "./pages/AIMeeting";
import Profile from "./pages/Profile";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <AppLayout>
                <Dashboard />
              </AppLayout>
            }
          />
          <Route
            path="/companies"
            element={
              <AppLayout>
                <Companies />
              </AppLayout>
            }
          />
          <Route
            path="/followup"
            element={
              <AppLayout>
                <Followup />
              </AppLayout>
            }
          />
          <Route
            path="/followup/:id"
            element={
              <AppLayout>
                <FollowupDetail />
              </AppLayout>
            }
          />
          <Route
            path="/todos"
            element={
              <AppLayout>
                <Todos />
              </AppLayout>
            }
          />
          <Route
            path="/schedules"
            element={
              <AppLayout>
                <Schedules />
              </AppLayout>
            }
          />
          <Route
            path="/calendar"
            element={
              <AppLayout>
                <CalendarPage />
              </AppLayout>
            }
          />
          <Route
            path="/history"
            element={
              <AppLayout>
                <History />
              </AppLayout>
            }
          />
          <Route
            path="/reports"
            element={
              <AppLayout>
                <Reports />
              </AppLayout>
            }
          />
          <Route
            path="/funnel"
            element={
              <AppLayout>
                <Funnel />
              </AppLayout>
            }
          />
          <Route
            path="/products"
            element={
              <AppLayout>
                <Products />
              </AppLayout>
            }
          />
          <Route
            path="/documents"
            element={
              <AppLayout>
                <Documents />
              </AppLayout>
            }
          />
          <Route
            path="/mailbox"
            element={
              <AppLayout>
                <Mailbox />
              </AppLayout>
            }
          />
          <Route
            path="/cards"
            element={
              <AppLayout>
                <BusinessCards />
              </AppLayout>
            }
          />
          <Route
            path="/ai-meeting"
            element={
              <AppLayout>
                <AIMeeting />
              </AppLayout>
            }
          />
          <Route
            path="/profile"
            element={
              <AppLayout>
                <Profile />
              </AppLayout>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
