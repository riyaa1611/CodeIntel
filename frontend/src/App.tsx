import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import PRDetail from './pages/PRDetail'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/repos/:repoId/reviews/:reviewId" element={<PRDetail />} />
      </Routes>
    </BrowserRouter>
  )
}
