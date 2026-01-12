import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import SkillsPage from './pages/SkillsPage';
import SkillDetailPage from './pages/SkillDetailPage';
import DocsPage from './pages/DocsPage';
import SubmitPage from './pages/SubmitPage';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/skills" element={<SkillsPage />} />
        <Route path="/skills/:skillId" element={<SkillDetailPage />} />
        <Route path="/docs" element={<DocsPage />} />
        <Route path="/submit" element={<SubmitPage />} />
      </Routes>
    </Layout>
  );
}

export default App;
