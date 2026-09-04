import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { AppsPage } from "@/pages/apps";
import { BreakfastPage } from "@/pages/breakfast";
import { Chat } from "@/pages/chat";
import { CiPage } from "@/pages/ci";
import { Commits } from "@/pages/commits";
import { Dashboard } from "@/pages/dashboard";
import { DiscoveryPage } from "@/pages/discovery";
import { HelpPage } from "@/pages/help";
import { InboxPage } from "@/pages/inbox";
import { Issues } from "@/pages/issues";
import { Lectures } from "@/pages/lectures";
import { LogsPage } from "@/pages/logs";
import { PullRequests } from "@/pages/pull-requests";
import { Repositories } from "@/pages/repos";
import { Settings } from "@/pages/settings";
import { StarsPage } from "@/pages/stars";
import { ToolsPage } from "@/pages/tools";

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
          <Route path="/stars" element={<StarsPage />} />
          <Route path="/commits" element={<Commits />} />
          <Route path="/inbox" element={<InboxPage />} />
          <Route path="/breakfast" element={<BreakfastPage />} />
          <Route path="/ci" element={<CiPage />} />
          <Route path="/discovery" element={<DiscoveryPage />} />
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
