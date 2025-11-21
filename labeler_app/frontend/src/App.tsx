import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { ProjectsPage } from './pages/ProjectsPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { DatasetPage } from './pages/DatasetPage'
import { LabelerPage } from './pages/LabelerPage'

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/projects" replace />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/:projectId" element={<ProjectDetailPage />} />
        <Route path="datasets/:datasetId" element={<DatasetPage />} />
        <Route path="datasets/:datasetId/label" element={<LabelerPage />} />
        <Route path="*" element={<Navigate to="/projects" replace />} />
      </Route>
    </Routes>
  )
}

export default App
