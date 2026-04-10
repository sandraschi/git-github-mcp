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

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/repos" element={<Repositories />} />
          <Route path="/commits" element={<Commits />} />
          <Route path="/inbox" element={<InboxPage />} />
          <Route path="/issues" element={<Issues />} />
          <Route path="/prs" element={<PullRequests />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/lectures" element={<Lectures />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
