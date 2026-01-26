import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AdminPage } from './AdminPage.js';
import App from './App.js';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function Router() {
  // Handle GitHub Pages routing
  const search = window.location.search;
  if (search.startsWith('?/')) {
    const path = search.slice(2);
    window.history.replaceState(null, '', path || '/');
  }
  
  const path = window.location.pathname;
  
  if (path.includes('/admin') || path === '/System-Design-Playground/admin') {
    return <AdminPage />;
  }
  
  return <App />;
}

export default function AppWithRouter() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router />
    </QueryClientProvider>
  );
}