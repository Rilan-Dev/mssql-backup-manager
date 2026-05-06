
import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import { AuthProvider } from "./context/AuthContext"
import Connect from "./pages/Connect"
import Dashboard from "./pages/Dashboard"
import DatabaseDetails from "./pages/DatabaseDetails"

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Connect />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/database/:dbName" element={<DatabaseDetails />} />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
