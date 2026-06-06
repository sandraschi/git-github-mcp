import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/app-layout';
import { Dashboard } from '@/pages/dashboard';
import { Repositories } from '@/pages/repos';
import { Commits } from '@/pages/commits';
import { Issues } from '@/pages/issues';
import { PullRequests } from '@/pages/pull-requests';
import { Chat } from '@/pages/chat';
import { Settings } from '@/pages/settings';
import { Lectures } from '@/pages/lectures';
import { InboxPage } from '@/pages/inbox';
import { BreakfastPage } from '@/pages/breakfast';
import { ToolsPage } from '@/pages/tools';
import { LogsPage } from '@/pages/logs';
import { HelpPage } from '@/pages/help';
import { AppsPage } from '@/pages/apps';

function App() {
  return (
    <Router>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tools" element={<ToolsPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/apps" element={<AppsPage />} />
          <Route path="/help" element={<HelpPage />} />
          <Route path="/repos" element={<Repositories />} />
          <Route path="/commits" element={<Commits />} />
          <Route path="/inbox" element={<InboxPage />} />
          <Route path="/breakfast" element={<BreakfastPage />} />
          <Route path="/issues" element={<Issues />} />
          <Route path="/prs" element={<PullRequests />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/lectures" element={<Lectures />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
